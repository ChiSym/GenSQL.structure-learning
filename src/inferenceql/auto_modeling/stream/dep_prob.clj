(ns inferenceql.auto-modeling.stream.dep-prob
  "Utility functions related to dep-prob."
  (:refer-clojure :rename {reduce reduce-core})
  (:require [cheshire.core :as json]
            [inferenceql.inference.utils :refer [average]]))

(defn reduce-dp-maps [dp-jsons]
  (let [cols (-> dp-jsons first keys)]
    (into {}
          (for [c1 cols]
            [c1 (into {}
                      (for [c2 (remove #{c1} cols)]
                        (let [vals (map #(get-in % [c1 c2]) dp-jsons)
                              avg-dp (average vals)]
                          [c2 avg-dp])))]))))

(defn reduce
  [{:keys [dep-prob]}]
  (let [dep-prob (-> dep-prob str slurp (json/parse-string true))
        ;; Group dep-prob results for iteration.
        dp-trans (apply map vector dep-prob)]
    (print (json/generate-string (map reduce-dp-maps dp-trans)
                                 {:pretty true}))))
