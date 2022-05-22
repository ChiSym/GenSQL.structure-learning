(ns inferenceql.auto-modeling.query-server
  "Start an SPN server to run queries against an automatically built model."
  (:require [libpython-clj2.python :as python]
            [inferenceql.gpm.spn :as spn]
            [inferenceql.query.io :as qio]
            [inferenceql.query.db :as db]
            [inferenceql.query.server :as server]
            [inferenceql.query :as query]
            [ring.adapter.jetty :as jetty]))

; XXX do I still need this?
(defn rem-empty [row]
  (into {}
        (remove #(clojure.string/blank? (str (val %))))
        row))

(def data (map rem-empty (qio/slurp-csv "data/data.csv")))
(def model_spn (spn/slurp "data/sppl/merged.json"))

(def db (as-> (if false
                "pass"
                (db/empty))
          %
          (reduce-kv db/with-table % {:data data})
          (reduce-kv db/with-model % {:model model_spn})))

(defn run [_]
  (println "starting server...")
  (let [app (server/app db)]
    (jetty/run-jetty app {:port 3000 :join? false}))
  (println "... server is running!")
  (println "   Please visit https://observablehq.com/@iql/query-data-and-models-v001"))
