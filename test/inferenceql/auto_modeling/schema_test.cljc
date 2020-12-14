(ns inferenceql.auto-modeling.schema-test
  (:require [inferenceql.auto-modeling.schema :as schema]
            [clojure.test :as test :refer [deftest is]]))

(deftest nullify
 (let [data [{:a 0.1,   :b "x"},
             {:a 1.0,   :b "999"},
             {:a 2.1,   :b "y"},
             {:a 3.4,   :b "x"},
             {:a "NaN", :b "x"}]
       null-vals #{"NaN", "999"}
       nullified-data [{:a 0.1, :b "x", },
                       {:a 1.0},
                       {:a 2.1, :b "y", },
                       {:a 3.4, :b "x", },
                       {:b "x"}]]
  (is (= nullified-data (schema/nullify data null-vals)))))

(deftest schema
  (let [data [{:a 0.1  , :b "x", :c  1, :d  "2020-01-28", :e  "same"},
              {:a 1.0  , :b "y", :c  2, :d  "2020-01-27", :e  "same"},
              {:a 2.1  , :b "y", :c  3, :d  "2020-01-28", :e  "same"},
              {:a 3.4  , :b "x", :c  4, :d  "2020-01-29", :e  "same"},
              {:a "NaN", :b "x", :c  5, :d  "2020-01-23", :e  "same"}]
        nullified-data (schema/nullify data #{"NaN"})
        ignore #{:d}
        nominal #{:c}]
    (is (= {:a "numerical", :b "nominal", :c "ignore", :d "nominal" :e "ignore"}
           (schema/guess-schema nullified-data)))
    (is (= {:a "numerical", :b "nominal", :c "ignore", :d "ignore" :e "ignore"}
           (schema/guess-schema nullified-data ignore)))
    (is (= {:a "numerical", :b "nominal", :c "nominal", :d "ignore" :e "ignore"}
           (schema/guess-schema nullified-data ignore nominal)))))
