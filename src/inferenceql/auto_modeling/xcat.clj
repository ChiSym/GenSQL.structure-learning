(ns inferenceql.auto-modeling.xcat
  (:refer-clojure :exclude [import])
  (:require [cheshire.core :as json]
            [clojure.data.csv :as csv]
            [clojure.edn :as edn]
            [inferenceql.auto-modeling.csv :as am.csv]
            [inferenceql.inference.gpm.crosscat :as crosscat]
            [medley.core :as medley]))

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

(defn ^:private fix-cgpm-maps
  "Converts lists of pairs in CGPM model cgpm to maps."
  [cgpm]
  (let [->map #(into {} %)]
    (-> cgpm
        (update :view_alphas ->map)
        (update :Zv ->map)
        (update :Zrv ->map))))

(defn ^:private data
  [data-cells schema]
  (let [headers (map keyword (first data-cells))
        column->f (comp {:numerical am.csv/parse-number
                         :nominal str}
                        schema
                        name)]
    (zipmap (range)
            (map #(-> (zipmap headers %)
                      (am.csv/update-by-key column->f))
                 (rest data-cells)))))

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

(defn ^:private spec
  [numericalized schema cgpm-model]
  (let [columns (mapv keyword (first numericalized))
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

(defn ^:private options
  [mapping-table]
  (->> mapping-table
       (medley/map-keys keyword)
       (medley/map-vals #(->> % (sort-by val) (map key) (into [])))))

(defn import
  [{:keys [cgpm-json data-csv mapping-table numericalized-csv schema-edn]}]
  (let [schema        (-> schema-edn        (str) (slurp) (edn/read-string))
        mapping-table (-> mapping-table     (str) (slurp) (edn/read-string))
        csv-data      (-> data-csv          (str) (slurp) (csv/read-csv))
        numericalized (-> numericalized-csv (str) (slurp) (csv/read-csv))
        cgpm-model    (-> cgpm-json         (str) (slurp) (json/parse-string true) (fix-cgpm-maps))

        data (data csv-data schema)
        spec (spec numericalized schema cgpm-model)
        latents (latents cgpm-model)
        options (options mapping-table)
        model (crosscat/construct-xcat-from-latents spec latents data {:options options})]
    (prn model)))
