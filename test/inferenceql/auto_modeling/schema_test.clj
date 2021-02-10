(ns inferenceql.auto-modeling.schema-test
  (:require [inferenceql.auto-modeling.schema :as schema]
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
                            {:x 2 :y "c"}]))))

(deftest guess-stattype
  (are [stattype coll] (= stattype (schema/guess-stattype coll))
    :ignore    [0 0 0]
    :ignore    [1 2 3]
    :nominal   [1 "2" 3]
    :numerical [0.0 1.0 2.0]))

(deftest guess
  (is (= {:id :ignore
          :x :numerical
          :y :nominal}
         (schema/guess
          [{:id 0 :x 0.0 :y "a"}
           {:id 1 :x 1.0 :y "b"}
           {:id 2 :x 2.0 :y "c"}]))))

(deftest loom
  (is (= {:x "nich"
          :y "dd"}
         (schema/loom {:id :ignore
                       :x :numerical
                       :y :nominal}))))
