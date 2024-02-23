(ns inferenceql.structure-learning.main
  (:import [java.io PushbackReader])
  (:require [babashka.fs :as fs]
            [cheshire.core :as json]
            [clj-yaml.core :as yaml]
            [clojure.data.csv :as csv]
            [clojure.edn :as edn]
            [clojure.java.io :as io]
            [clojure.string :as string]
            [inferenceql.structure-learning.csv :as iql.csv]
            [inferenceql.structure-learning.dvc :as dvc]
            [inferenceql.inference.gpm :as gpm]
            [inferenceql.query.db :as db]
            [inferenceql.query.io :as query.io]
            [medley.core :as medley]))

(defn nullify [_]
  (let [null-vals (set (:nullify (dvc/yaml)))
        nullify-row (fn [row]
                      (mapv #(when-not (contains? null-vals %)
                               %)
                            row))
        [headers & rows] (csv/read-csv *in*)]
    (->> (conj (map nullify-row rows)
               headers)
         (csv/write-csv *out*))))

(defn numericalize
  [{table-path :table schema-path :schema}]
  (let [schema (edn/read-string (slurp (str schema-path)))
        nominal-columns (into #{}
                              (comp (filter (comp #{:nominal} val))
                                    (map key))
                              schema)
        numericalizers (zipmap nominal-columns
                               (repeatedly iql.csv/numericalizer))
        [columns & rows] (csv/read-csv *in*)
        numericalize-row (fn [row]
                           (map (fn [column val]
                                  (if (string/blank? val)
                                    ""
                                    (if-let [numericalize (get numericalizers column)]
                                      (numericalize val)
                                      val)))
                                columns
                                row))
        numericalized-csv (conj (map numericalize-row rows) columns)]
    (csv/write-csv *out* numericalized-csv)
    (let [table (medley/map-vals (fn [f] (f)) numericalizers)]
      (spit (io/file (str table-path))
            table))))

(defn sample-count
  [_]
  (-> (slurp *in*)
      (yaml/parse-string)
      (get-in [:loom :sample_count])
      (print)))

(defn infer-config
  [_]
  (let [yaml (-> (slurp *in*)
                 (yaml/parse-string))
        seed (get-in yaml [:seed])
        extra-passes (get-in yaml [:loom :extra_passes])
        config {:schedule {:extra_passes extra-passes
                           :seed seed}}]
    (json/generate-stream config *out*)))

(defmulti read-model fs/extension)

(defmethod read-model "json"
  [file]
  (let [slurp-spn (requiring-resolve 'inferenceql.gpm.sppl/slurp)]
    (slurp-spn file)))

(defmethod read-model "edn"
  [file]
  (edn/read {:readers gpm/readers} (PushbackReader. (io/reader file))))

(defn assemble-database
  {:org.babashka.cli
   {:coerce {:table-name :symbol
             :model-name :symbol
             :table-path :file
             :model-path :file}}}
  [{:keys [table-name table-path model-name model-path]}]
  (prn (cond-> (db/empty)
         (and table-name
              table-path)
         (db/with-table table-name (query.io/slurp-csv table-path))

         (and model-name
              model-path)
         (db/with-model model-name (read-model model-path)))))
