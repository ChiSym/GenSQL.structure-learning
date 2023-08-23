(ns inferenceql.auto-modeling.csv
  (:refer-clojure :exclude [dissoc])
  (:require [clojure.edn :as edn]
            [inferenceql.auto-modeling.vector :as vector]))

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

(defn numericalizer
  "Returns a stateful numericalization function. When called with 1 argument the
  function will return a unique integer for that value. Subsequent calls to the
  function on the same value will return the same integer. When called with 0
  arguments the function will return a map from values to their unique integers
  across all invocations of the function. After the function has been called
  with 0 arguments subsequent calls to the function will throw an exception."
  []
  (let [i (volatile! 0)
        x->n (volatile! (transient {}))]
    (fn
      ([]
       (persistent! @x->n))
      ([x]
       (when-not (contains? @x->n x)
         (vswap! x->n assoc! x @i)
         (vswap! i inc))
       (get @x->n x)))))

(defn dissoc
  ([csv] csv)
  ([csv k]
   (let [headers (first csv)
         index (.indexOf headers k)]
     (if-not (nat-int? index)
       csv
       (map #(vector/remove-nth % index)
            csv))))
  ([csv k & ks]
   (let [csv (dissoc csv k)]
     (if ks
       (recur csv (first ks) (next ks))
       csv))))

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
