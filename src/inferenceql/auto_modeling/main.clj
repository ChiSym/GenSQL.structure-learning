(ns inferenceql.auto-modeling.main
  (:require [cheshire.core :as json]
            [clj-yaml.core :as yaml]
            [clojure.data.csv :as csv]
            [clojure.edn :as edn]
            [clojure.java.io :as io]
            [clojure.string :as string]
            [inferenceql.auto-modeling.csv :as iql.csv]
            [inferenceql.auto-modeling.dvc :as dvc]
            [inferenceql.auto-modeling.schema :as schema]
            [medley.core :as medley]))

(defn nullify
  [_]
  (let [null-vals (set (:nullify (dvc/yaml)))]
    (->> (csv/read-csv (slurp *in*))
         (iql.csv/as-maps)
         (map #(medley/remove-vals (some-fn nil? null-vals) %))
         (iql.csv/as-cells)
         (csv/write-csv *out*))))

(defn guess-schema
  [_]
  (let [params-schema (:schema (dvc/yaml))
        guessed-schema (->> (csv/read-csv (slurp *in*))
                            (iql.csv/as-maps)
                            (map #(medley/remove-vals (every-pred string? string/blank?) %))
                            (iql.csv/heuristic-coerce-all)
                            (map #(medley/remove-keys (set (keys params-schema)) %))
                            (schema/guess))
        schema (merge guessed-schema params-schema)]
    (prn schema)))

(defn loom-schema
  [_]
  (-> (slurp *in*)
      (edn/read-string)
      (schema/loom)
      (json/generate-stream *out*)))

(defn cgpm-schema
  [_]
  (-> (slurp *in*)
      (edn/read-string)
      (schema/cgpm)
      (pr)))

(defn iql-viz-schema
  [_]
  (-> (slurp *in*)
      (edn/read-string)
      (schema/iql-viz)
      (pr)))

(defn numericalize
  [{table-path :table schema-path :schema}]
  (let [nominal-columns (into #{}
                              (comp (filter (comp #{:nominal} val))
                                    (map key))
                              (edn/read-string (slurp (io/file (str schema-path)))))
        {:keys [rows table]} (->> (csv/read-csv (slurp *in*))
                                  (iql.csv/as-maps)
                                  (medley/remove-vals (some-fn nil? (every-pred string? string/blank?)))
                                  (iql.csv/heuristic-coerce-all)
                                  (iql.csv/numericalize nominal-columns))]

    (spit (io/file (str table-path))
          table)

    (->> rows
         (iql.csv/as-cells)
         (csv/write-csv *out*))))

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

(defn param
  [{:keys [key]}]
  (if-let [result (get-in (dvc/yaml)
                          (into []
                                (map (comp keyword name))
                                (string/split (str key) #"\.")))]
    (print result)
    (System/exit 1)))
