(ns inferenceql.structure-learning.clojurecat
  "Utility functions related to the ClojureCat command-line interface."
  (:refer-clojure :exclude [merge])
  (:require [clojure.java.io :as io]
            [clojure.pprint :refer [pprint]]
            [inferenceql.inference.gpm :as gpm]
            [inferenceql.inference.gpm.ensemble :as ensemble]))

(defn config
  "Outputs a config file for use with the clojurecat command-line interface."
  [{:keys [iterations]}]
  (pprint {:model :xcat
           :n-infer-iters iterations}))

(defn merge
  "Merges the GPMs in a directory."
  [{path :models out :out}]
  (let [path (str path)
        out (str out)]
    (->> (io/file path)
         (file-seq)
         (filter #(.isFile %))
         (map slurp)
         (map gpm/read-string)
         (ensemble/ensemble)
         (pr-str)
         (spit out))))
