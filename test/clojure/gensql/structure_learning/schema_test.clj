(ns gensql.structure-learning.schema-test
  (:require [gensql.structure-learning.schema :as schema]
            [clojure.test :as test :refer [deftest are is]]))

(deftest consecutive?
  (are [bool coll] (= bool (schema/consecutive? coll))
    true  [0 1 2]
    true  [2]
    true  [1 2 3]
    false [0 2 3]))

(deftest column
  (is (= [0 1 2]
         (schema/column :x [{:x 0 :y "a"}
                            {:x 1 :y "b"}
                            {:x 2 :y "c"}])))
  (is (= [0 1 2]
         (schema/column "x" [{"x" 0 "y" "a"}
                             {"x" 1 "y" "b"}
                             {"x" 2 "y" "c"}]))))

(deftest guess-stattype
  (are [stattype coll] (= stattype (schema/guess-stattype :ignore coll))
    :ignore    [0 0 0]
    :ignore    [1 2 3]
    :nominal   [1 "2" 3]
    :numerical [0.0 1.0 2.0]
    :ignore    (map #(str "x" %) (range 51))))


(deftest guess
  (is (= {:id :ignore
          :x :numerical
          :y :nominal}
         (schema/guess
           :ignore
          [{:id 0 :x 0.0 :y "a"}
           {:id 1 :x 1.0 :y "b"}
           {:id 2 :x 2.0 :y "c"}])))
  (is (= {"id" :ignore
          "x" :numerical
          "y" :nominal}
         (schema/guess
           :ignore
           [{"id" 0 "x" 0.0 "y" "a"}
            {"id" 1 "x" 1.0 "y" "b"}
            {"id" 2 "x" 2.0 "y" "c"}]))))

(deftest loom
  (is (= {:x "nich"
          :y "dd"}
         (schema/loom {:id :ignore
                       :x :numerical
                       :y :nominal})))
  (is (= {"x" "nich"
          "y" "dd"}
         (schema/loom {"id" :ignore
                       "x" :numerical
                       "y" :nominal}))))
