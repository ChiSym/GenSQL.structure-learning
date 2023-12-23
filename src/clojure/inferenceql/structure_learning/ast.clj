(ns inferenceql.structure-learning.ast)

(defn columns
  [ast]
  (sort
   (into []
         (comp (mapcat :view/clusters)
               (mapcat (comp keys :cluster/column->distribution))
               (distinct))
         (:multimixture/views ast))))

(defn transduce-views
  [ast xf]
  (update ast
          :multimixture/views
          (fn [views]
            (into (empty views)
                  xf
                  views))))

(defn transduce-clusters
  [ast xf]
  (transduce-views
   ast
   (map (fn [view]
          (update view
                  :view/clusters
                  (fn [clusters]
                    (into (empty clusters)
                          xf
                          clusters)))))))

(defn empty-cluster?
  [cluster]
  (empty? (:cluster/column->distribution cluster)))

(defn empty-view?
  [view]
  (every? empty-cluster? (:view/clusters view)))

(defn select-columns
  [ast columns]
  (-> ast
      (transduce-clusters (map #(update % :cluster/column->distribution select-keys columns)))
      (transduce-views (remove empty-view?))))
