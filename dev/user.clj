(ns user
  (:require [clojure.tools.namespace.repl :as repl]
            [com.stuartsierra.component :as component]
            [inferenceql.auto-modeling.webapp :as webapp]))

(def system nil)

(defn nilsafe
  "Returns a function that calls f on its argument if its argument is not nil."
  [f]
  (fn [x]
    (when x
      (f x))))

(defn new-system
  []
  (-> (component/system-map
       :dvc (webapp/dvc "dvc.yaml")
       :web-server (webapp/jetty-server :port 8080))
      (component/system-using
       {:web-server [:dvc]})))

(defn init
  "Constructs the current development system."
  []
  (alter-var-root #'system (fn [_] (new-system))))

(defn start
  "Starts the current development system."
  []
  (alter-var-root #'system component/start))

(defn stop
  "Shuts down and destroys the current development system."
  []
  (alter-var-root #'system (nilsafe component/stop)))

(defn go
  "Initializes the current development system and starts it running."
  []
  (init)
  (start))

(defn reset []
  (stop)
  (repl/refresh :after 'user/go))

(comment

  (-> (:dvc system) :state deref :process :exit)

  (go)
  (reset)
  (stop)
  (start)

  system

  (webapp/start-run! (:dvc system))

  (webapp/stop-run! (:dvc system))

  (webapp/running? (:dvc system))

  (webapp/pipeline-status (:dvc system))

  ,)
