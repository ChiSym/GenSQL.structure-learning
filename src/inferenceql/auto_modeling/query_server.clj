(ns inferenceql.auto-modeling.query-server
  "Start an SPN server to run queries against an automatically built model."
  (:require [clojure.data.json :as json]
            [clojure.edn :as edn]
            [clojure.java.io :as java.io]
            [clojure.string :as string]
            [inferenceql.gpm.spn :as spn]
            [inferenceql.query.io :as io]
            [inferenceql.query.db :as db]
            [inferenceql.query.server :as server]
            [ring.adapter.jetty :as jetty]))

(defn rem-empty [row]
  (into {}
        (remove #(string/blank? (str (val %))))
        row))

(def model-name 'model)

(def model-name-column 'model_name)

(def c1-name (symbol "column_1"))
(def c2-name (symbol "column_2"))

(def data (map rem-empty (io/slurp-csv "data/data.csv")))

(def model_spn (spn/slurp "data/sppl/merged.json"))

(def schema (edn/read (java.io.PushbackReader. (java.io/reader "data/schema.edn"))))

(def schema-table
  (map (fn [[k v]]
         {'column (name k)
          'statistical_type (name v)
          model-name-column model-name})
       schema))

(defn safe-get [c1 c2 d]
  (if (contains? (get d c1) c2)
    (get (get d c1) c2)
    (get (get d c2) c1)))

(defn same? [d]
  (= (get d c1-name)
     (get d c2-name)))

(def deps-table
  (let [modeled-cols (map key (remove (comp #{:ignore} val) schema))
        deps (json/read-str (slurp "data/dep-prob.json"))]
    (remove same? (reduce into
                          []
                          (map (fn [c1] (map (fn [c2]
                                               {c1-name c1
                                                c2-name c2
                                                model-name-column model-name
                                                'probability_predictive (safe-get c1 c2 deps)})
                                             modeled-cols))
                               modeled-cols)))))

(def cors-table
  (let [num-cols (map key (filter (comp #{:numerical} val) schema))
        cors (json/read-str (slurp "data/correlation.json"))]
    (remove same? (reduce into
                          []
                          (map (fn [c1] (map (fn [c2]
                                               {c1-name c1
                                                c2-name c2
                                                model-name-column "linear"
                                                'r (get (safe-get c1 c2 cors) "r-value")
                                                'p (get (safe-get c1 c2 cors) "p-value")})
                                             num-cols))
                               num-cols)))))

(def db (as-> (if false
                "pass"
                (db/empty))
          %
          (reduce-kv db/with-table % {:data data
                                      :schema schema-table
                                      :correlations cors-table
                                      :predictive_relationships deps-table
                                      (keyword model-name) model_spn})))

(defn run [{:keys [lang] :as m}]
  (println (str "starting server with language: " lang))
  (let [app (server/app db :lang lang)]
    (jetty/run-jetty app {:port 3000 :join? false}))
  (println "... server is running!")
  (println "   Please visit https://observablehq.com/@iql/query-data-and-models-v001"))
