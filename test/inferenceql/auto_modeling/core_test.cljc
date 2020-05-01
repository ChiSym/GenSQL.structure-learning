(ns inferenceql.auto-modeling.core-test
  (:require [clojure.test :refer [deftest is]]
            [inferenceql.auto-modeling.core :as auto-modeling]))

(deftest smoke
  (is (boolean? (auto-modeling/flip))))
