(ns inferenceql.auto-modeling.heatmap
  "Functions for generating dependence probability heatmaps."
  (:require [clojure.data.json :as json])
  (:import [smile.clustering HierarchicalClustering]
           [smile.clustering.linkage UPGMCLinkage]))

;; The challenge when generating a dependence probability heatmap is finding a
;; column ordering that will position columns that have a high probability of
;; being dependent next to one another. To generate this ordering we use
;; agglomerative clustering. The agglomerative clustering algorithm works as
;; follows:

;; We generate a tree of clusters from the bottom up. At the bottom of the tree
;; each item is in its own cluster. To generate the next level in the tree we
;; merge the two closest pairs of clusters, where closeness is determinted by a
;; distance metric we define. We repeat this process until we generate the top
;; of the tree, where there is only one cluster.

(defn- columns
  "Returns all the columns in a dependence probability JSON."
  [json]
  (set (keys json)))

(defn- prob-dependent
  "Returns a function that will return the dependence probability between two
  columns according to the provided dependence probability JSON."
  [json]
  (fn [col1 col2]
    (double
     (if (= col1 col2)
       1.0
       (get-in json [col1 col2] 0.0)))))

(defn- clustering-comp
  "Returns a comparator function for use with `clojure.core/sort` that will sort
  columns according to their dependence probability clustering."
  [json]
  ;; We use an agglomerative clustering algorithm from the Smile machine
  ;; learning library. For our distance metric (the distance between columns) we
  ;; use the probability that the columns are dependent. Columns that have a
  ;; higer probability of dependence are considered closer together.
  (let [prob-dependent (prob-dependent json)
        ;; Smile's distance metrics require that you provide the distance
        ;; between each pair of values as a two-dimensional array of doubles,
        ;; where the value at coordinate (x, y) in the array is the distance
        ;; between the items at index x and index y.
        columns (vec (columns json))
        linkage (UPGMCLinkage/of
                 (into-array
                  (for [c1 (range (count columns))]
                    (double-array
                     (for [c2 (range (count columns))]
                       (let [col1 (nth columns c1)
                             col2 (nth columns c2)]
                         (prob-dependent col1 col2)))))))
        clustering (HierarchicalClustering/fit linkage)]
    ;; The `HierarchicalClustering` class provides a method, `partition`, which
    ;; cuts the tree into n groups. `partition` returns an integer array where
    ;; each integer represents a unique cluster assignment for the item (in our
    ;; case, column) at that index. We define a comparator which cuts the tree
    ;; into successively larger sets of clusters until the columns of interest
    ;; are in different clusters. The comparator then compares the unique
    ;; integers for the two clusters.
    (fn [col1 col2]
      (loop [n-clusters 2]
        (if (>= n-clusters (count columns))
          false
          (let [clusters (vec (.partition clustering n-clusters))
                c1i (.indexOf columns col1)
                c2i (.indexOf columns col2)
                c1s (nth clusters c1i)
                c2s (nth clusters c2i)]
            (if (= c1s c2s)
              (recur (inc n-clusters))
              (> c1s c2s))))))))

(defn- column-order
  "Sorts columns according to their dependence probability clustering."
  [json]
  (let [columns (columns json)
        clustering-comp (clustering-comp json)]
    (->> columns
         (sort clustering-comp)
         (vec))))

(defn- dep-prob-rows
  "Returns a sequence of maps each of which refers to a pair of columns and
  their dependence probability."
  [json]
  (let [prob-dependent (prob-dependent json)
        columns (columns json)]
    (for [col1 columns
          col2 columns]
      {:col1 col1
       :col2 col2
       :dep-prob (prob-dependent col1 col2)})))

(defn- dep-prob-spec
  "Returns a Vega-Lite spec for a dependence probability heatmap."
  [json]
  (let [column-order (column-order json)]
    {:$schema "https://vega.github.io/schema/vega-lite/v5.json"
     :data {:values (dep-prob-rows json)}
     :mark {:type "rect"
            :tooltip true}
     :encoding {:x {:title false
                    :field "col1"
                    :type "nominal"
                    :sort column-order}
                :y {:title false
                    :field "col2"
                    :type "nominal"
                    :sort column-order}
                :color {:field "dep-prob"
                        :type "quantitative"
                        :scale {:domain [0.0 1.0]
                                :scheme "blues"}}}}))

(defn dep-prob
  "Prints a Vega-Lite spec for a dependence probability heatmap."
  [& {:keys [json-path]}]
  (let [json (-> (slurp json-path)
                 (json/read-str))
        spec (dep-prob-spec json)]
    (json/write spec *out*)))
