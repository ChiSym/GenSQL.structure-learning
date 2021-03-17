(ns inferenceql.auto-modeling.csv
  (:require [clojure.data.csv :as csv]
            [clojure.edn :as edn]
            [clojure.pprint :as pprint]))

(defn parse-number
  "Attempts to parse string s as a number or `nil`. Throws a
  `java.lang.NumberFormatException` if parsing fails."
  [s]
  (let [x (edn/read-string s)]
    (if (or (number? x)
            (nil? x))
      x
      (throw (NumberFormatException. (str "The value " (pr-str x) " cannot be read as a number or nil."))))))

(defn as-maps
  ([coll]
   (as-maps coll {}))
  ([coll opts]
   (let [{:keys [key-fn]} opts
         headers (cond->> (first coll)
                   key-fn (map key-fn))]
     (into []
           (map #(zipmap headers %))
           (rest coll)))))

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

(defn heuristic-coerce
  [& coll]
  (try (into []
             (map #(if (nil? %)
                     %
                     (Long/parseLong %)))
             coll)
       (catch java.lang.NumberFormatException _
         (try (into []
                    (map #(if (nil? %)
                            %
                            (Double/parseDouble %)))
                    coll)
              (catch java.lang.NumberFormatException _
                coll)))))

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

(defn update-by-key
  "For each key k in coll if (f k) returns a function update the value for k in
  coll with that function."
  [coll f]
  (reduce-kv (fn [coll k v]
               (if-let [f (f k)]
                 (assoc coll k (f v))
                 coll))
             coll
             coll))
