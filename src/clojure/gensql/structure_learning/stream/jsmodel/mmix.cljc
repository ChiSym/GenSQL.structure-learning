(ns gensql.structure-learning.stream.jsmodel.mmix
  "Functions for transforming a multimix model spec into template data for passing to
  a mustache template that displays a javascript representation of the model spec."
  (:require [clojure.string :as str]
            [medley.core :as medley]
            #?(:cljs [goog.string :refer [format]])))

(defn trunc
  "Truncate number to 3 decimals places."
  [n]
  (if (integer? n)
    (str n)
    (format "%.3f" n)))

(def range-1
  "Infinite list of natural numbers."
  (map inc (range)))

(defn maybe-quote
  "Add string escaped quotes to `category` if it is a string."
  [category]
  (if (string? category)
    (str "\"" category "\"")
    category))

(defn categorical-col-vals
  "Returns a map of categorical cols and their values given a multimix `spec`.
  The map returned maps from col name to a sequence of col values for that category."
  [spec]
  (let [;; First cluster from all views merged.
        first-clusters (->> (get-in spec [:views])
                            (map first)
                            (map :parameters)
                            (apply merge))
        categorical-cols (keys (medley/filter-vals #(= % :categorical)
                                                   (get-in spec [:vars])))]
    (into {}
      (for [col categorical-cols]
        (let [cat-values (keys (get first-clusters col))]
          [col cat-values])))))

(defn categories-section
  "Returns data for the categories section of the js-model-template.
  Takes a multimix `spec`."
  [spec]
  (for [[col cat-vals] (categorical-col-vals spec)]
    {:name (name col)
     :values (str/join ", " (map maybe-quote cat-vals))}))

(defn model-section
  "Returns data for the model section of the js-model-template.
  Takes a multimix `spec`."
  [spec]
  (let [num-views (count (get spec :views))
        view-numbers (take num-views range-1)]
    {:view-fn-nums view-numbers
     :splats (for [vn view-numbers]
               {:num vn :last (= vn num-views)})}))

(defn parameters-section
  "Returns data for the parameters section of a cluster for the js-model-template.

  Takes `parameters` which is a map of column name to parameter values.
  (These parameters are exactly as they apppear under the :parameters key of a multimix spec.)

  Takes `categorical-col-vals`, which is a mapping of column name to allowed column values for
  each categorical column."
  [parameters categorical-col-vals]
  (let [num-params (count parameters)]
    (for [[index [param-key param-vals]] (map vector range-1 parameters)]
      (case (some? (get categorical-col-vals param-key))
        true ;; Categorical variable.
        {:name (name param-key)
         :last (= index num-params)
         :categorical true
         ;; We need to produce a string of the category weights in a consistent order.
         :weights (->> (get categorical-col-vals param-key)
                       (map param-vals)
                       (map trunc)
                       (str/join ", "))}

        false ;; Guassian variable.
        {:name (name param-key)
         :last (= index num-params)
         :gaussian true
         :mu (trunc (:mu param-vals))
         :sigma (trunc (:sigma param-vals))}))))

(defn views-section
  "Returns data for the views section of the js-model-template."
  [spec]
  (let [categorical-col-vals (categorical-col-vals spec)
        views (get-in spec [:views])]
    (for [[view-num view] (map vector range-1 views)]
      {:num view-num
       :cluster-probs (str/join ", " (map (comp trunc :probability) view))
       :clusters (for [[cluster-num cluster] (map vector range-1 view)]
                   {:first (= cluster-num 1)
                    :num cluster-num
                    :parameters (parameters-section (get cluster :parameters)
                                                    categorical-col-vals)})})))

(defn template-data
  "Produces template data to be passed to our js-model mustache template.
  Takes a multimix model `spec`."
  [spec]
  {:categories (categories-section spec)
   :model (model-section spec)
   :views (views-section spec)})

