(ns inferenceql.auto-modeling.csv-test
  (:refer-clojure :exclude [dissoc])
  (:require [clojure.test :refer [is deftest]]
            [clojure.test.check.clojure-test :refer [defspec]]
            [clojure.test.check.generators :as gen]
            [clojure.test.check.properties :as prop]
            [inferenceql.auto-modeling.csv :as csv]))


(deftest as-maps
  (is (= [] (sequence (csv/as-maps) [])))
  (is (= [] (sequence (csv/as-maps) [[:a :b :c]])))
  (is (= [{:a 1 :b 2 :c 3} {:a 4 :b 5 :c 6}]
         (sequence (csv/as-maps) [[:a :b :c] [1 2 3] [4 5 6]]))))

(deftest as-cells
  (is (= [] (sequence (csv/as-cells) [])))
  (is (= [[:a :b :c] [0 1 2]] (sequence (csv/as-cells) [{:a 0 :b 1 :c 2}])))
  (is (= [[:a :b :c] [1 2 3] [4 5 6]]
         (sequence (csv/as-cells) [{:a 1 :b 2 :c 3} {:a 4 :b 5 :c 6}]))))

(defspec round-trip
  (let [max-cols 10
        gen-header gen/keyword
        gen-value gen/small-integer]
    (prop/for-all [coll (gen/let [header-row (gen/not-empty (gen/vector-distinct gen-header {:max-elements max-cols}))
                                  rows (gen/not-empty (gen/vector (gen/vector gen-value (count header-row))))]
                          (into [header-row] rows))]
      (is (= coll
             (sequence (comp (csv/as-maps)
                             (csv/as-cells))
                       coll))))))

(deftest dissoc
  (let [csv [[:a :b :c]
             [0 1 2]
             [0 1 2]
             [0 1 2]]]
    (is (= csv (csv/dissoc csv)))
    (is (= [[:b :c]
            [1 2]
            [1 2]
            [1 2]]
           (csv/dissoc csv :a)))
    (is (= [[:a :c]
            [0 2]
            [0 2]
            [0 2]]
           (csv/dissoc csv :b)))
    (is (= [[:a :b]
            [0 1]
            [0 1]
            [0 1]]
           (csv/dissoc csv :c)))
    (is (= [[:a]
            [0]
            [0]
            [0]]
           (csv/dissoc csv :b :c)))
    (is (= [[:b]
            [1]
            [1]
            [1]]
           (csv/dissoc csv :a :c)))
    (is (= [[:c]
            [2]
            [2]
            [2]]
           (csv/dissoc csv :a :b)))
    (is (= [[]
            []
            []
            []]
           (csv/dissoc csv :a :b :c)))))
