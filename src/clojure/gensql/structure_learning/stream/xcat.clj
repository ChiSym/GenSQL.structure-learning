(ns gensql.structure-learning.stream.xcat
  "Defs used by various DVC stages dealing with Xcat records."
  (:refer-clojure :exclude [import])
  (:require [cheshire.core :as json]
            [clojure.data.csv :as csv]
            [clojure.edn :as edn]
            [gensql.structure-learning.stream.transit :as transit]
            [gensql.structure-learning.stream.xcat.sample :as xcat.sample]
            [gensql.structure-learning.stream.xcat.spec :as xcat.spec]
            [gensql.structure-learning.xcat :as am.xcat]
            [gensql.structure-learning.dvc :as dvc]
            [clojure.java.io :as io]
            [clojure.string :as string]))

(def pretty-printer
  (json/create-pretty-printer
   (assoc json/default-pretty-print-options :indent-arrays? true)))

(defn transitions-import
  "Converts a json array of cgpm-model exports (transitions) into xcat-records.
  The output is a json array of strings. Each string is a transit-encoded xcat record."
  [{:keys [transitions-path data-csv mapping-table numericalized-csv schema-edn]}]
  (let [schema        (-> schema-edn        (str) (slurp) (edn/read-string))
        mapping-table (-> mapping-table     (str) (slurp) (edn/read-string))
        csv-data      (-> data-csv          (str) (slurp) (csv/read-csv))
        numericalized (-> numericalized-csv (str) (slurp) (csv/read-csv))

        cgpm-transitions (-> transitions-path str io/reader (json/parse-stream true))
        xcat-string (fn [transition]
                      (let [cgpm (am.xcat/fix-cgpm-maps transition)
                            xcat (am.xcat/xcat-model cgpm schema mapping-table csv-data numericalized)]
                        (transit/string xcat)))
        transit-strings (map xcat-string cgpm-transitions)]
    (json/generate-stream transit-strings *out* {:pretty pretty-printer})))

(defn transitions-merge
  "Merges xcat-records for multiples xcat transitions files.
  Takes the transit-encoded xcat record at each iteration in each transitions file and
  combines them into a json array representing an ensemble in the output. Output will be a json
  array of ensembles.

  Args:
    `transitions-paths - a string of paths to xcat transitions json files. Paths are separated by
      newlines."
  [{:keys [transitions-paths]}]
  (let [paths (-> transitions-paths (string/split #"\n"))
        jsons (map #(json/parse-stream (io/reader %) true) paths)
        ensembles (apply map vector jsons)]
    (json/generate-stream ensembles *out* {:pretty pretty-printer})))

(defn transitions-sample
  "Samples 1000 points from the ensemble of xcat models at each iteration. Each sample is
  produced using a model chosen randomly from the ensemble. The collection of samples produced
  is a transit-encoded string of a clojure collection of samples at each iteration."
  [{:keys [transitions-merged schema-edn]}]
  (let [schema (-> schema-edn (str) (slurp) (edn/read-string))
        ensembles (json/parse-stream (io/reader (str transitions-merged)) true)

        num-points 1000
        allow-neg (:allow_negative_simulations (dvc/stream-yaml))
        samples (pmap #(xcat.sample/sample-ensemble num-points schema allow-neg %) ensembles)]
    (json/generate-stream (transit/string samples) *out* {:pretty pretty-printer})))

(defn transitions-shorten-ensemble
  "Shortens the size of each ensemble in the sequence of ensembles provided. Each ensemble is
  shortened to only have 3 xcat models. In addition, the individual models are no longer
  transit-encoded xcat records. They are now transit-encoded latents that can be used to instantiate
  an xcat-record. This is to save space, as xcat records have the whole dataset inside the record.
  The output is again a json array consisting of ensembles (array of transit-strings)."
  [{:keys [transitions-merged]}]
  (let [ensembles (json/parse-stream (io/reader (str transitions-merged)) true)
        ensembles-short (vec (for [e ensembles]
                               (let [transit-strings (take 3 e)
                                     xcats (map transit/reify transit-strings)
                                     specs (map xcat.spec/xcat->full-spec xcats)
                                     transit-strings (map transit/string specs)]
                                 (vec transit-strings))))]
    (json/generate-stream ensembles-short *out* {:pretty pretty-printer})))
