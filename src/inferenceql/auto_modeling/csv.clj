(ns inferenceql.auto-modeling.csv
  (:require [clojure.data.csv :as csv]
            [clojure.pprint :as pprint]))

(defn as-maps
  [coll]
  (let [[headers & rows] coll]
    (into []
          (map #(zipmap headers %))
          rows)))

(defn as-cells
  [coll]
  (let [headers (into #{}
                      (mapcat keys)
                      coll)]
    (into [(vec headers)]
          (map (fn [row]
                 (reduce (fn [acc header]
                           (conj acc (get row header)))
                         []
                         headers)))
          coll)))

(defn nullify
  "Remove null values."
  [values data]
  (map (fn [row]
         (into {}
               (remove (comp values val))
               row))
       data))

(defn lookup-table
  "Constructs a lookup table for a sequence of maps `ms`, which maps each "
  [ks ms]
  (zipmap (sort (into []
                      (comp (keep #(get % ks))
                            (distinct))
                      ms))
          (iterate inc 0)))

(defn numericalize
  [columns rows]
  (let [table (zipmap columns
                      (map #(lookup-table % rows)
                           columns))
        rows (mapv (fn [row]
                     (reduce (fn [row column]
                               (cond-> row
                                 (contains? row column) (update column (get table column))))
                             row
                             columns))
                   rows)]
    {:rows rows
     :table table}))

(defn numericalize-csv
  [{:keys [columns out]}]
  (with-open [reader *in*]
    (let [rows (as-maps (csv/read-csv reader))
          {:keys [rows table]} (numericalize columns rows)]
      (spit (str out) table)
      (pprint/pprint rows))))

;; This was a one-off fucntion we used to create test data.
(defn new-csv
  [_]
  (let [[headers & rows] (csv/read-csv (slurp "/Users/zane/Desktop/data.csv"))
        new-headers (into ["id"] headers)
        output (into [new-headers]
                     (map-indexed (fn [index row]
                                    (into [index] row))
                                  rows))]
    (csv/write-csv *out* output)))

(defn heuristic-coerce
  [& coll]
  (try (into []
             (map #(if (nil? %)
                     %
                     (Integer/parseInt %)))
             coll)
       (catch java.lang.NumberFormatException _
         (try (into []
                    (map #(if (nil? %)
                            %
                            (Double/parseDouble %)))
                    coll)
              (catch java.lang.NumberFormatException _
                coll)))))

#_(heuristic-coerce "1" "2" nil "3")

(defn apply-column
  [k f coll]
  (let [new-column (->> coll
                        (map #(get % k))
                        (apply f))]
    (map-indexed (fn [index m]
                   (let [v (get new-column index)]
                     (cond-> m
                       (some? v) (assoc k v))))
                 coll)))

(defn heuristic-coerce-all
  [coll]
  (let [ks (into #{}
                 (mapcat keys)
                 coll)]
    (reduce (fn [acc k]
              (apply-column k heuristic-coerce acc))
            coll
            ks)))

#_(apply-column
   :x
   (fn [& ns]
     (map (fnil inc 0) ns))
   [{:x 0 :y 1}
    {:y 2}
    {:x 2 :y 3}])
