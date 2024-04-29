(ns gensql.structure-learning.stream.xcat.sample
  "Utility functions for sampling x-cat models."
  (:require [gensql.structure-learning.stream.xcat.util :refer [sample-xcat]]
            [gensql.structure-learning.stream.transit :as transit]))

(defn add-null-columns [row schema]
  (let [columns (map name (keys schema))
        null-kvs (zipmap columns (repeat nil))]
    (merge null-kvs row)))

(defn sample-ensemble [num-points schema allow-neg model-strings]
  (let [num-models (count model-strings)
        models (atom {})]
    (for [_i (range num-points)]
      (let [model-index (rand-int num-models)]
        (when-not (contains? @models model-index)
          (let [model (transit/reify (nth model-strings model-index))]
            (swap! models assoc model-index model)))
        (let [model (get @models model-index)]
          (-> (sample-xcat model 1 {:allow-neg allow-neg})
              (first)
              (add-null-columns schema)))))))
