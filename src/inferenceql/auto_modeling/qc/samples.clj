(ns inferenceql.auto-modeling.qc.samples
  (:require [clojure.edn :as edn]
            [clojure.pprint :refer [pprint]]
            [inferenceql.inference.gpm :as gpm]
            [inferenceql.query.io :as io]))


(defn tag
  "Adds a collection attribute to both observed data and simulated data."
  [{data-path :data samples-synthetic-path :samples-synthetic}]
  (let [data (map #(update-keys % keyword) (io/slurp-csv (str data-path)))
        samples-synthetic (-> samples-synthetic-path str slurp edn/read-string)
        out (concat (map #(assoc % :collection "synthetic") samples-synthetic)
                    (map #(assoc % :collection "observed") (take (count samples-synthetic) (shuffle data))))]
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
