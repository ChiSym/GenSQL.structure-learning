(ns inferenceql.auto-modeling.dvc
  (:require [clj-yaml.core :as yaml]))

(defn yaml
  []
  (-> (slurp "params.yaml")
      (yaml/parse-string)
      (update :nullify set)
      (update :schema (fn [schema]
                        (into {}
                              (map (juxt (comp name key)
                                         (comp keyword val)))
                              schema)))
      (update-in [:qc :columns] (fn [columns] (seq (map keyword columns))))))
