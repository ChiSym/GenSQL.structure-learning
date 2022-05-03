(ns inferenceql.auto-modeling.qc.samples
  (:require [clojure.edn :as edn]
            [clojure.pprint :refer [pprint]]
            [inferenceql.inference.gpm :as gpm]
            [inferenceql.query.data :refer [row-coercer]]
            [inferenceql.query.io :as io]
            [medley.core :as medley]))

(defn tag
  "Adds a collection attribute to both observed data and simulated data."
  [{data-path :data schema-path :schema samples-virtual-path :samples-virtual}]
  (let [schema (-> schema-path str slurp edn/read-string)
        coercer (row-coercer (medley/map-keys keyword schema))
        data (mapv coercer (-> data-path str io/slurp-csv))

        samples-virtual (-> samples-virtual-path str slurp edn/read-string)

        out (concat (map #(assoc % :collection "virtual") samples-virtual)
                    (map #(assoc % :collection "observed") data))]
    (pprint out)))

(defn sample-xcat
  "Samples all targets from an XCat gpm."
  [{:keys [model data sample-count]}]
  (let [model (-> model str slurp gpm/read-string)
        data (-> data str io/slurp-csv)
        sample-count (or sample-count (count data))

        targets (gpm/variables model)
        simulations (repeatedly sample-count #(gpm/simulate model targets {}))]
    (pprint simulations)))
