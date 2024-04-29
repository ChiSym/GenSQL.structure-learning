(ns gensql.structure-learning.stream.mmix
  (:refer-clojure :exclude [import])
  (:require [cheshire.core :as json]
            [gensql.structure-learning.stream.transit :as transit]
            [gensql.inference.gpm.crosscat :as xcat]
            [clojure.java.io :as io]))

(def pretty-printer
  (json/create-pretty-printer
   (assoc json/default-pretty-print-options :indent-arrays? true)))

(defn transitions-import
  "Converts seq of transit-encoded xcat models into seq of transit-encoded mmix specs."
  [{:keys [transitions-path]}]
  (let [transitions (-> transitions-path str io/reader (json/parse-stream true))
        mmix (fn [transit-string]
               (let [xcat-model (transit/reify transit-string)]
                 (xcat/xcat->mmix xcat-model)))
        mmixs (map mmix transitions)]
    (json/generate-stream (transit/string mmixs) *out* {:pretty pretty-printer})))
