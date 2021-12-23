(ns inferenceql.auto-modeling.xcat
  "Defs for producing XCat records from CGPM export JSONs."
  (:refer-clojure :exclude [import])
  (:require [cheshire.core :as json]
            [clojure.data.csv :as csv]
            [clojure.edn :as edn]
            [medley.core :as medley]
            [inferenceql.auto-modeling.csv :as am.csv]
            [inferenceql.inference.gpm.crosscat :as xcat]))

(defn ^:private view-name
  "Returns a cluster name for view index n."
  [n]
  (keyword (str "view_" n)))

(defn ^:private cluster-name
  "Returns a cluster name for cluster index n."
  [n]
  (keyword (str "cluster_" n)))

(defn ^:private map-invert
  "Returns m with its vals as keys and its keys grouped into a vector as vals."
  [m]
  (->> (group-by second m)
       (medley/map-vals #(mapv key %))))

(defn fix-cgpm-maps
  "Converts lists of pairs in CGPM model cgpm to maps."
  [cgpm]
  (let [->map #(into {} %)]
    (-> cgpm
        (update :view_alphas ->map)
        (update :Zv ->map)
        (update :Zrv ->map))))

(defn ^:private data
  [data-cells schema num-rows]
  (let [headers (map keyword (first data-cells))
        column->f (comp {:numerical am.csv/parse-number
                         :nominal am.csv/parse-str}
                        schema
                        name)
        rows (map #(-> (zipmap headers %)
                       (am.csv/update-by-key column->f))
                  (rest data-cells))]
    (zipmap (range) (take num-rows rows))))

(defn ^:private views
  [columns {:keys [hypers Zv]}]
  (let [column->hypers (zipmap columns hypers)]
    (->> Zv
         (medley/map-keys columns)
         (medley/map-vals view-name)
         (map-invert)
         (medley/map-vals (fn [columns]
                            {:hypers (zipmap columns
                                             (map column->hypers columns))})))))

(defn ^:private col-names
  [numericalized cgpm-model]
  (mapv keyword (get cgpm-model :col_names (first numericalized))))

(defn ^:private spec
  [numericalized schema cgpm-model]
  (let [columns (col-names numericalized cgpm-model)
        views (views columns cgpm-model)
        types (->> schema
                   (medley/map-keys keyword)
                   (medley/map-vals {:nominal :categorical
                                     :numerical :gaussian}))]
    {:views views
     :types types}))

(defn ^:private latents
  [{:keys [alpha Zrv] view-alphas :view_alphas}]
  (let [local (merge-with merge
                          (->> view-alphas
                               (medley/map-keys view-name)
                               (medley/map-vals (fn [alpha] {:alpha alpha})))
                          (->> Zrv
                               (medley/map-keys view-name)
                               (medley/map-vals (fn [clusters]
                                                  (let [y (zipmap (range)
                                                                  (map cluster-name clusters))
                                                        counts (->> y
                                                                    (group-by second)
                                                                    (medley/map-vals count))]
                                                    {:counts counts
                                                     :y y})))))]
    {:global {:alpha alpha}
     :local local}))

(defn options
  [mapping-table]
  (->> mapping-table
       (medley/map-keys keyword)
       (medley/map-vals #(->> % (sort-by val) (map key) (into [])))))

(defn xcat-model
  "Returns a XCat record given a CGPM model and other necessary items."
  [cgpm-model schema mapping-table csv-data numericalized]
  (let [data (data csv-data schema (-> cgpm-model :X count))
        spec (spec numericalized schema cgpm-model)
        latents (latents cgpm-model)
        options (options mapping-table)]
    (xcat/construct-xcat-from-latents spec latents data {:options options})))

(defn import
  "Imports a CGPM model (json) and prints it out as an XCat record (edn)."
  [{:keys [cgpm-json data-csv mapping-table numericalized-csv schema-edn]}]
  (let [schema        (-> schema-edn        (str) (slurp) (edn/read-string))
        mapping-table (-> mapping-table     (str) (slurp) (edn/read-string))
        csv-data      (-> data-csv          (str) (slurp) (csv/read-csv))
        numericalized (-> numericalized-csv (str) (slurp) (csv/read-csv))
        cgpm-model    (-> cgpm-json         (str) (slurp) (json/parse-string true) (fix-cgpm-maps))]
    (prn (xcat-model cgpm-model schema mapping-table csv-data numericalized))))
