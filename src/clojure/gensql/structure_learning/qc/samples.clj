(ns gensql.structure-learning.qc.samples
  (:require [clojure.pprint :refer [pprint]]
            [gensql.inference.gpm :as gpm]
            [gensql.query.io :as io]))


(defn tag
  "Adds a collection attribute to both observed data and simulated data."
  [{data-path :data samples-synthetic-path :samples-synthetic}]
  (let [data (map #(update-keys % keyword) (io/slurp-csv (str data-path)))
        samples-synthetic (map #(update-keys % keyword) (io/slurp-csv (str samples-synthetic-path)))
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
