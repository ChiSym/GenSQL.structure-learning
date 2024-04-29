(ns gensql.structure-learning.stream.xcat.util
  "Various utility functions dealing with Xcat records."
  (:require [medley.core :as medley]
            [gensql.inference.gpm :as gpm]
            [clojure.set]))

(defn columns-in-model [xcat]
  (let [views (-> xcat :views vals)
        columns-in-view (fn [view] (-> view :columns keys))]
    (mapcat columns-in-view views)))

(defn numerical-columns
  "Returns columns names with type :gaussian in `xcat`."
  [xcat]
  (let [col-gpms (->> xcat :views vals (map :columns) (apply merge))
        col-types (medley/map-vals :stattype col-gpms)]
    (keys (medley/filter-vals #{:gaussian} col-types))))

(defn sample-xcat
  "Samples all targets from an XCat gpm. `n` is the number of samples."
  ([xcat n]
   (sample-xcat xcat n {}))
  ([xcat n {:keys [allow-neg]}]
   (let [targets (gpm/variables xcat)
         simulate #(gpm/simulate xcat targets {})

         ;; Returns a function that checks `row` for negative values in the keys
         ;; provided as `cols`.
         neg-check (fn [cols]
                     (fn [row]
                       (some neg? (vals (select-keys row cols)))))

         neg-row? (cond
                    (= allow-neg nil)
                    (neg-check (numerical-columns xcat))

                    (= allow-neg false)
                    (neg-check (numerical-columns xcat))

                    (= allow-neg true)
                    (constantly false)

                    (and (seq? allow-neg)
                         (empty? allow-neg))
                    (neg-check (numerical-columns xcat))

                    (seq allow-neg)
                    (let [cols-to-check
                          (clojure.set/difference
                           (set (numerical-columns xcat))
                           (set (map keyword allow-neg)))]
                      (neg-check cols-to-check)))]
     (take n (remove neg-row? (repeatedly simulate))))))

(defn col-ordering
  "Ordering of columns as they appear in the sequence of model iterations."
  [xcat-stream]
  (reduce (fn [ordering xcat]
            (let [new-columns (clojure.set/difference (set (columns-in-model xcat))
                                                      (set ordering))]
              (into []
                    (concat ordering new-columns))))
          []
          xcat-stream))

(defn num-rows-at-iter
  "Number of rows used at each model iteration."
  [xcat-stream]
  (mapv (fn [xcat]
          (let [[_view-1-name view-1] (first (get xcat :views))]
            ;; Count the number of row to cluster assignments.
            (count (get-in view-1 [:latents :y]))))
        xcat-stream))

