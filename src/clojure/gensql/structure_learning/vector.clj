(ns gensql.structure-learning.vector)

(defn remove-nth
  [coll n]
  (into (subvec coll 0 n)
        (subvec coll (inc n))))
