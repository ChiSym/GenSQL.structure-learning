(ns inferenceql.auto-modeling.main
  (:import [java.io PushbackReader])
  (:require [babashka.fs :as fs]
            [cheshire.core :as json]
            [clj-yaml.core :as yaml]
            [clojure.data.csv :as csv]
            [clojure.edn :as edn]
            [clojure.java.io :as io]
            [clojure.string :as string]
            [inferenceql.auto-modeling.csv :as iql.csv]
            [inferenceql.auto-modeling.dvc :as dvc]
            [inferenceql.auto-modeling.schema :as schema]
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

(defn guess-schema
  [_]
  (let [params (dvc/yaml)
        params-schema (:schema params)
        default-stattype (get params :default-stat-type  :ignore)
        guessed-schema (->> (csv/read-csv *in*)
                            (sequence (comp (iql.csv/as-maps)
                                            (map #(medley/remove-vals (every-pred string? string/blank?) %))
                                            (map #(medley/remove-keys (set (keys params-schema)) %))))
                            (iql.csv/heuristic-coerce-all)
                            (schema/guess default-stattype))
        schema (merge guessed-schema params-schema)]
    (assert (not (every? #{:ignore} (vals schema)))
            "The statistical types of the columns in data.csv can't be guessed confidently.\nAll columns are ignored. Set statistical types manually in params.yaml to fix this")
    (prn schema)))

(defn loom-schema
  [_]
  (-> (edn/read *in*)
      (schema/loom)
      (json/generate-stream *out*)))

(defn cgpm-schema
  [_]
  (-> (edn/read *in*)
      (schema/cgpm)
      (pr)))

(defn ignore
  [{:keys [schema]}]
  (let [ignored (into #{}
                      (comp (filter (comp #{:ignore} val))
                            (map key))
                      (edn/read-string (slurp schema)))
        csv (csv/read-csv *in*)
        ignored-csv (apply iql.csv/dissoc csv ignored)]
    (csv/write-csv *out* ignored-csv)))

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
