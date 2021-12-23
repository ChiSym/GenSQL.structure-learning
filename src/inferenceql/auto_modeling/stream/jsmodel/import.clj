(ns inferenceql.auto-modeling.stream.jsmodel.import
  (:require [inferenceql.auto-modeling.stream.jsmodel.mmix :as mmix]
            [clojure.java.io :as io]
            [cheshire.core :as json]
            [cljstache.core :refer [render]]
            [clojure.string :as string]
            [inferenceql.auto-modeling.stream.transit :as transit]))

(def pretty-printer
  (json/create-pretty-printer
   (assoc json/default-pretty-print-options :indent-arrays? true)))

(def js-program-template (slurp "resources/templates/model.js.mustache"))

(defn js-program [mmix]
  (render js-program-template
          (mmix/template-data mmix)))

(defn transitions-import
  [{:keys [transitions-path]}]
  (let [mmixs (-> transitions-path str io/reader (json/parse-stream true) transit/reify)
        js-programs (map js-program mmixs)]
    (json/generate-stream js-programs *out* {:pretty pretty-printer})))

(defn transitions-merge
  [{:keys [transitions-paths]}]
  (let [paths (-> transitions-paths (string/split #"\n"))
        jsons (map #(json/parse-stream (io/reader %) true) paths)
        ensembles (apply map vector jsons)]
    (json/generate-stream ensembles *out* {:pretty pretty-printer})))
