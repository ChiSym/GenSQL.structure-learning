(ns inferenceql.auto-modeling.clojurecat
  "Utility functions related to the ClojureCat command-line interface."
  (:require [clojure.pprint :refer [pprint]]))

(defn config
  "Outputs a config file for use with the clojurecat command-line interface."
  [{:keys [iterations]}]
  (pprint {:model :xcat
           :n-infer-iters iterations}))

