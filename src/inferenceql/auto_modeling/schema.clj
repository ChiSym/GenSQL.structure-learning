(ns inferenceql.auto-modeling.schema
  (:require [clojure.set]))

(defn consecutive?
  "Returns true if if the provided column is comprised entirely of consecutive integers."
  [coll]
  (let [sorted-coll (sort coll)]
    (= sorted-coll
       (take (count coll)
             (iterate inc (first sorted-coll))))))

(defn column
  "Given a key k and a collection of associative data structures coll, `column`
  returns a sequence of the values in for key k. Returns a transducer if only a
  key is provided."
  ([k]
   (map #(get % k)))
  ([k coll]
   (sequence (column k) coll)))

(defn guess-stattype
  "Guess the statistical type of a collection of values."
  [coll]
  (let [max-categories 50
        dv (distinct coll) ; Distinct vals.
        num-dv (count dv)
        ratio-dv (/ num-dv (count coll)) ; Ratio of distinct vals to all vals.

        ;; Number of distinct values below which columns whose values can all be parsed as
        ;; numbers will be considered nominal anyway.
        numcat-count 20
        ;; Ratio of distinct values to total values below which columns whose values can
        ;; all be parsed as numbers will be considered nominal anyway.
        numcat-ratio 0.02]
    (cond (= 1 num-dv)
          :ignore

          (some string? coll)
          (if (< num-dv max-categories)
            :nominal
            :ignore)

          (= num-dv (count coll))
          (if (every? integer? coll)
            (if (consecutive? coll)
              :ignore
              :numerical)
            :numerical)

          (every? number? coll)
          (if (or (< num-dv numcat-count)
                  (< ratio-dv numcat-ratio))
            :nominal
            :numerical)

          :else
          :ignore)))

(defn guess
  "Guess a schema for a collection of maps."
  [coll]
  (let [columns (into #{} (mapcat keys) coll)]
    (zipmap columns
            (map #(guess-stattype (column % coll))
                 columns))))

(defn loom
  "Returns the Loom schema for an InferenceQL schema."
  [schema]
  (let [replacements {:nominal "dd" ; discrete dirichlet
                      :numerical "nich"}] ; normal inverse chi squared
    (into {}
          (comp (remove (comp #{:ignore} val))
                (map (juxt key (comp replacements val))))
          schema)))

(defn cgpm
  "Returns the CGPM schema for an InferenceQL schema."
  [schema]
  (let [replacements {:nominal "categorical" ; discrete dirichlet
                      :numerical "normal"}]
    (into {}
          (comp (remove (comp #{:ignore} val))
                (map (juxt (comp  name key) (comp replacements val))))
          schema)))
