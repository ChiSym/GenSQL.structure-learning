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
  ;; XXX THIS IS FAR FROM COMPLETE!
  ;; Todo:
  ;; - look into percentage of values.
  ;; - double check https://github.com/probcomp/bayeslite/blob/master/src/guess.py#L227-L297
  (let [max-categories 50 ; XXX: choose better heuristic.
        num-disitinct-vals (count (distinct coll))]
    (cond (< num-disitinct-vals 2)
          :ignore

          (some string? coll)
          (if (< num-disitinct-vals max-categories)
            :nominal
            :ignore)

          (= num-disitinct-vals (count coll))
          (if (every? integer? coll)
            (if (consecutive? coll)
              :ignore
              :numerical)
            :numerical)

          (and (every? float? coll)
               (> num-disitinct-vals
                  (/ (count coll)
                     2)))

          :numerical
          :else (throw (ex-info "Could not resolve stattype"
                                {:coll coll})))))

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
