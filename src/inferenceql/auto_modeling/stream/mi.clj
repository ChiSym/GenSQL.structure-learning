(ns inferenceql.auto-modeling.stream.mi
  "Utility functions related to mutual information."
  (:refer-clojure :rename {reduce reduce-core})
  (:require [cheshire.core :as json]
            [inferenceql.inference.utils :refer [average]]))

(defn reduce-mi-maps [mi-jsons]
  (assert (apply = (map :configs mi-jsons)))
  (let [config (-> mi-jsons first :configs)
        mi-maps (map :mi mi-jsons)
        cols (-> mi-maps first keys)
        reduced-mi
        (into {}
              (for [c1 cols]
                [c1 (into {}
                          (for [c2 (remove #{c1} cols)]
                            (let [mi-vals (map #(get-in % [c1 c2]) mi-maps)
                                  avg-mi (average mi-vals)]
                              [c2 avg-mi])))]))]
    {:configs config
     :mi reduced-mi}))

(defn reduce
  "Reduce MI values accross CrossCat samples"
  [{:keys [mi]}]
  (let [mi (-> mi str slurp (json/parse-string true))
        ;; Group MI results for iteration.
        mi-trans (apply map vector mi)]
    (print (json/generate-string (map reduce-mi-maps mi-trans)
                                 {:pretty true}))))
