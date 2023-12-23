(ns inferenceql.structure-learning.stream.config
  "Defs for creating a config.edn file for iql.viz.stream."
  (:refer-clojure :exclude [import])
  (:require [cheshire.core :as json]
            [clojure.edn :as edn]
            [clojure.pprint :as pprint]
            [medley.core :as medley]
            [inferenceql.structure-learning.stream.xcat.util :as util]
            [inferenceql.structure-learning.stream.transit :as transit]
            [inferenceql.structure-learning.xcat :as am.xcat]
            [inferenceql.structure-learning.dvc :as dvc]
            [clojure.java.io :as io])
  (:import (java.io Writer)))

;;; The following defs are used to maintain tags in edn files with custom-tagged elements--in
;;; particular in the iql.viz.stream config.edn template. Normally, reading in edn with custom tag
;;; removes them, we want to preserve them when the edn is written back out.
;;; See this for more: https://github.com/clojure-cookbook/clojure-cookbook/blob/master/04_local-io/4-17_unknown-reader-literals.asciidoc

(defrecord TaggedValue [tag value])

(defmethod print-method TaggedValue [this ^Writer w]
  (.write w "#")
  (print-method (:tag this) w)
  (.write w " ")
  (print-method (:value this) w))

(defn pprint-tagged-value [tg]
  (print "#")
  (print (:tag tg))
  (print " ")
  (pr (:value tg)))

(def pprint-d
  (. pprint/simple-dispatch addMethod TaggedValue pprint-tagged-value))

(defn generate
  "Generates a config.edn file for iql.viz.stream. Builds off of pre-existing config.edn template,
  and adds in inforamtion of model transitions under :transitions and general app settings under
  :settings."
  [{:keys [transitions-merged mapping-table config]}]
  (let [mapping-table (-> mapping-table (str) (slurp) (edn/read-string))
        ensembles (json/parse-stream (io/reader (str transitions-merged)) true)

        first-stream (vec (for [e ensembles]
                            (transit/reify (first e))))

        get-column-dependencies (fn [xcat]
                                  (->> (get-in xcat [:latents :z])
                                       (group-by val)
                                       (medley/map-vals #(map first %))
                                       (sort-by key)
                                       (map second)
                                       (mapv (comp vec sort))))

        column-dependencies (vec (for [e ensembles]
                                   (vec (for [t-string e]
                                          (let [xcat (transit/reify t-string)]
                                            (get-column-dependencies xcat))))))
        num-modeled-columns (fn [xcat]
                              (-> xcat :latents :z keys count))

        config-new {:transitions {:count (count first-stream)
                                  :columns-at-iter (mapv num-modeled-columns first-stream)
                                  :num-rows-at-iter (util/num-rows-at-iter first-stream)
                                  :column-ordering (util/col-ordering first-stream)
                                  :column-dependencies column-dependencies
                                  :options (am.xcat/options mapping-table)}
                    :settings (dvc/stream-yaml)}

        config-old (->> config str slurp (edn/read-string {:default ->TaggedValue}))
        config-updated (merge config-old config-new)]
    ;; Prints nicely and maintains tagged items.
    (binding [pprint/*print-pprint-dispatch* pprint-d
              pprint/*print-right-margin* 100
              pprint/*print-miser-width* 100]
      (pprint/pprint config-updated))))
