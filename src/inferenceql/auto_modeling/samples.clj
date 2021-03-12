(ns inferenceql.auto-modeling.samples
  (:require [clojure.edn :as edn]
            [clojure.pprint :refer [pprint]]
            [inferenceql.query.main :refer [slurp-csv]]
            [inferenceql.query.data :refer [row-coercer]]))

(defn tag [{data-path :data schema-path :schema samples-virtual-path :samples-virtual}]
  (let [schema (-> schema-path str slurp edn/read-string)
        coercer (row-coercer schema)
        data (mapv coercer (-> data-path str slurp-csv))

        samples-virtual (-> samples-virtual-path str slurp edn/read-string)

        out (concat (map #(assoc % :collection "virtual") samples-virtual)
                    (map #(assoc % :collection "observed") data))]
    (pprint out)))
