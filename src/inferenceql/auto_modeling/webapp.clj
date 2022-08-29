(ns inferenceql.auto-modeling.webapp
  (:require [babashka.process :as process]
            [clj-yaml.core :as yaml]
            [clojure.java.io :as io]
            [clojure.stacktrace :as stacktrace]
            [com.stuartsierra.component :as component]
            [lambdaisland.regal :as regal]
            [reitit.ring :as ring]
            [reitit.ring.middleware.exception :as exception]
            [ring.adapter.jetty :as jetty]
            [ring.middleware.format :refer [wrap-restful-format]]
            [ring.middleware.format-response :refer [wrap-restful-response]]
            [ring.util.response :as response]))

(defn read-yaml
  [path]
  (yaml/parse-string (slurp path)))

(comment

  (yaml/generate-string {:name "Zane"} :dumper-options {:flow-style :block})
  (yaml/generate-string [{:a 1 :b 2}])

  (require '[flatland.ordered.map :as ordered.map])
  (yaml/generate-string (ordered.map/ordered-map :name "Zane Matthews Shelby" :age 40))

  ,)

;;; DVC

(defn input-stream-atom
  [input-stream]
  (let [out (atom "")]
    (future
      (loop []
        (let [c (.read input-stream)]
          (when (not= c -1)
            (swap! out str (char c))
            (recur)))))
    out))

(declare map->DVC)

(defn dvc
  [path]
  (map->DVC {:yaml-path path
             :run (atom nil)}))

(defn start-run! [dvc]
  (let [{:keys [out err] :as process} (process/process "nix-shell --run 'dvc repro -f'")
        out (-> (io/reader out)
                (input-stream-atom))
        err (-> (io/reader err)
                (input-stream-atom))]
    (reset! (:run dvc)
            {:yaml (read-yaml "dvc.yaml")
             :process process
             :out out
             :err err})
    dvc))

(defn stop-run!
  [dvc]
  (when-let [process (some-> dvc :run deref :process :proc)]
    (.destroyForcibly process))
  (reset! (:run dvc) nil)
  dvc)

(defn running?
  [dvc]
  (if-let [run @(:run dvc)]
    (nil? (get-in run [:process :exit]))
    false))

(defrecord DVC [yaml-path run]
  component/Lifecycle
  (start [dvc]
    dvc)

  (stop [dvc]
    (stop-run! dvc)))

(defn parse-out
  "Parses DVC output into a map of stages, their output, and whether they have
  completed."
  ([s]
   (parse-out s nil))
  ([s exit-code]
   (let [stage-line [:cat "Running stage '"
                     [:capture [:+ [:not \']]]
                     "':" :newline]
         content-lines [:capture
                        [:+
                         [:cat
                          [:negative-lookahead "Running stage"]
                          [:* :any]
                          :newline]]]
         re (regal/regex
             [:cat
              stage-line
              content-lines
              [:? [:lookahead stage-line]]])]
     (into []
           (map (fn [[_ stage content next-stage]]
                  (let [status (if next-stage
                                 :succeeded
                                 (case exit-code
                                   0 :succeeded
                                   nil :in-progress
                                   :failed))]
                    {:name (keyword stage)
                     :out content
                     :status status})))
           (re-seq re s)))))

(defn update-stages
  [stages out]
  (let [steps (if-not out [] (parse-out out))]
    (->> (reduce (fn [stages {:keys [name] :as step}]
                   (update stages name into step))
                 stages
                 steps))))

(defn ordered-map->vector
  ([m]
   (ordered-map->vector m nil))
  ([m k]
   (reduce-kv (fn [coll k1 v]
                (conj coll
                      (if-not k v (assoc v k k1))))
              []
              m)))

(defn ordered-map->map
  [m]
  (into {} (seq m)))

(defn pipeline-status
  [dvc]
  (let [run @(:run dvc)
        yaml (if run
               (:yaml run)
               (read-yaml (:yaml-path dvc)))
        stages (:stages yaml)
        output-str (when run @(:out run))
        steps (->> (-> stages
                       (update-vals #(if (:status %)
                                       %
                                       (assoc % :status :not-started)))
                       (update-stages output-str)
                       (ordered-map->vector :name))
                   (map ordered-map->map))]
    {:steps steps}))

;;; Web server

(defn not-found-handler
  [_request]
  (-> (response/not-found "Not found")
      (response/header "Content-Type" "text/plain")))

(def exception-middleware
  (exception/create-exception-middleware
   (merge
    exception/default-handlers
    {::exception/default (fn [exception request]
                           {:status  500
                            :exception (with-out-str (stacktrace/print-stack-trace exception))
                            :uri (:uri request)
                            :body "Internal server error"})
     ::exception/wrap (fn [handler e request]
                        (println "ERROR" (pr-str (:uri request)))
                        (stacktrace/print-stack-trace e)
                        (flush)
                        (handler e request))})))

(defn page-handler
  [_]
  (response/response (slurp (io/resource "public/index.html"))))

(defn status-handler
  [dvc]
  (fn [_]
    (response/response (pipeline-status dvc))))

(defn start-handler
  [dvc]
  (fn [_]
    (if (running? dvc)
      {:status 409 :body "Already started"}
      (do (start-run! dvc)
          (response/created "/api/dvc" "Run started")))))

(defn stop-handler
  [dvc]
  (fn [_]
    (stop-run! dvc)
    {:status 204}))

(defn app
  [dvc]
  (ring/ring-handler
   (ring/router
    [["/" {:get page-handler}]
     ["/api" {:middleware [[wrap-restful-format :formats [:json]]
                           [wrap-restful-response]]}
      ["/dvc" {:get (#'status-handler dvc)
               :post (#'start-handler dvc)
               :delete (#'stop-handler dvc)}]]
     ["/js/*" (ring/create-resource-handler {:root "js"})]])
   #'not-found-handler
   {:middleware [exception-middleware]}))

(defrecord JettyServer [port dvc]
  component/Lifecycle

  (start [component]
    (let [handler (#'app dvc)
          jetty-server (jetty/run-jetty handler {:port port :join? false})]
      (assoc component :server jetty-server)))

  (stop [{:keys [server]}]
    (when server
      (.stop server))))

(defn jetty-server
  [& {:as opts}]
  (map->JettyServer opts))
