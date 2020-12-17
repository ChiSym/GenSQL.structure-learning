(ns inferenceql.auto-modeling.schema)

(defn consequitive-integers?
  "This function helps identify key columns."
  [col-vals]
  (let [sorted-vals (sort col-vals)]
    (= (last sorted-vals) 
       (dec
        (+ (first sorted-vals) 
           (count sorted-vals))))))

(defn guess-stattype
  "Guess the stattype for a given columnn."
  [data col]
  ;; XXX THIS IS FAR FROM COMPLETE!
  ;; Todo:
  ;; - look into percentage of values.
  ;; - double check https://github.com/probcomp/bayeslite/blob/master/src/guess.py#L227-L297
  (let [col-data (map #(get % col) data)
        distinct-vals (distinct col-data)
        n (count data)
        max-categories 50 ; XXX: choose better heuristic.
        num-disitinct-vals (count distinct-vals)]
        (cond
          (<  num-disitinct-vals 2) "ignore"
          (some string? col-data) (if (< num-disitinct-vals max-categories) "nominal" "ignore")
          (=  num-disitinct-vals (count data))
            (if (every? integer? col-data)
                  (if (consequitive-integers? col-data) "ignore" "numerical")
                  "numerical")
          (and (every? float? col-data) (> num-disitinct-vals (* 0.5 n))) "numerical"
          :else (throw (AssertionError. "Could not resolve stattype")))))

(defn guess-schema
  "Guess and overwrite a population schema."
  ([data]
    (guess-schema data #{} #{} #{}))
  ([data ignore-cols]
    (guess-schema data ignore-cols #{} #{}))
  ([data ignore-cols nominal-cols]
    (guess-schema data ignore-cols nominal-cols #{}))
  ([data ignore-cols nominal-cols numerical-cols]
  (let [col-names (into #{} (mapcat keys) data)]
    (into {}
          (map #(assoc {}
                       %
                       (cond (contains? ignore-cols %)    "ignore"
                             (contains? nominal-cols %)   "nominal"
                             (contains? numerical-cols %) "numerical"
                             :else (guess-stattype data %)))
               col-names)))))

(defn nullify
  "Remove null values."
  [data null-values]
  (map (fn [row](into {}
                      (remove (comp null-values val))
                      row))
       data))
