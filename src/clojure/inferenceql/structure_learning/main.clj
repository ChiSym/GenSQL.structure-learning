(ns inferenceql.structure-learning.main
  (:import [java.io PushbackReader])
  (:require [babashka.fs :as fs]
            [clojure.data.csv :as csv]
            [clojure.edn :as edn]
            [clojure.java.io :as io]
            [inferenceql.inference.gpm :as gpm]
            [inferenceql.query.db :as db]
            [inferenceql.query.io :as query.io]))


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
