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

(defn parse-str
  "Attempts to parse string s as a string  or
  `nil` if it sees the empty string."
  [s]
  (let [x (str s)] (if-not (= x "") x nil)))

(defn index-comparator
  "Returns a comparator that treats values that appear earlier in coll as less
  than values that appear later in coll."
  ([coll]
   (index-comparator coll ##Inf))
  ([coll missing]
   (fn [x y]
     (let [val->index (zipmap coll (range))
           f #(get val->index % missing)]
       (< (f x) (f y))))))

(defn as-maps
  "Returns a transducer that converts a sequence of vectors into a sequence of
  maps. The first element of the sequence is treated as keys to be `zipmap`ped
  with each subsequent element of the sequence."
  ([]
   (as-maps nil))
  ([empty]
   (fn [xf]
     (let [empty (atom empty)
           headers (atom nil)]
       (fn
         ([]
          (xf))
         ([result]
          (xf result))
         ([result input]
          (if-not @headers
            (do (reset! headers (vec input))
                (when-not @empty
                  (reset! empty (sorted-map-by (index-comparator @headers))))
                result)
            (xf result (into @empty (zipmap @headers input))))))))))

(defn as-cells
  "Returns a transducer that converts a sequence of maps into a two-dimensional
  vector by unzippping the map with the provided keys. If the 1-arity of the
  function is used the keys from the first map are used for each subsequent
  element in the sequence."
  ([]
   (as-cells nil))
  ([ks]
   (fn [xf]
     (let [ks (atom ks)
           ks-sent (atom false)]
       (fn
         ([]
          (xf))
         ([result]
          (xf result))
         ([result input]
          (when-not @ks
            (reset! ks (keys input)))
          (let [input (reduce (fn [acc header]
                                (conj acc (get input header)))
                              []
                              @ks)
                result (if @ks-sent
                         result
                         (do (reset! ks-sent true)
                             (xf result (vec @ks))))]
            (xf result input))))))))

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
