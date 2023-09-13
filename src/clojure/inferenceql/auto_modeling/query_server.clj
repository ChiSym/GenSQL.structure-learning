(ns inferenceql.auto-modeling.query-server
  "Start an SPN server to run queries against an automatically built model."
  (:require [clojure.data.json :as json]
            [clojure.edn :as edn]
            [clojure.java.io :as java.io]
            [clojure.string :as string]
            [inferenceql.gpm.sppl :as sppl]
            [inferenceql.query.db :as db]
            [inferenceql.query.io :as io]
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

(def model-spe (sppl/slurp "data/sppl/merged.json"))

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
  (let [deps-path "data/dep-prob.json"]
    (when (.exists (java.io/file deps-path))
      {:predictive_relationships
       (let [modeled-cols (map key (remove (comp #{:ignore} val) schema))
             deps (json/read-str (slurp deps-path))]
         (remove same? (reduce into
                               []
                               (map (fn [c1] (map (fn [c2]
                                                    {c1-name c1
                                                     c2-name c2
                                                     model-name-column model-name
                                                     'probability_predictive (safe-get c1 c2 deps)})
                                                  modeled-cols))
                                    modeled-cols))))})))

(def cors-table
  (let [cors-path "data/correlation.json"]
    (when (.exists (java.io/file cors-path))
      {:correlations
       (let [num-cols (map key (filter (comp #{:numerical} val) schema))
             cors (json/read-str (slurp cors-path))]
         (remove same? (reduce into
                               []
                               (map (fn [c1] (map (fn [c2]
                                                    {c1-name c1
                                                     c2-name c2
                                                     model-name-column "linear"
                                                     'r (get (safe-get c1 c2 cors) "r-value")
                                                     'p (get (safe-get c1 c2 cors) "p-value")})
                                                  num-cols))
                                    num-cols))))})))

(def db
  (let [db-map {:data data :schema schema-table (keyword model-name) model-spe}]
    (reduce-kv db/with-table (db/empty) (into (into db-map cors-table) deps-table))))

(defn run [_]
  (println "starting server...")
  (let [app (server/app db)]
    (jetty/run-jetty app {:port 3000 :join? false}))
  (println "... server is running!")
  (println "   Please visit https://observablehq.com/@iql/query-data-and-models-v001"))
