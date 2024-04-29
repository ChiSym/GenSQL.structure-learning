(ns ^:deprecated gensql.structure-learning.bayesdb-import-test
  (:require [clojure.test :refer [deftest is]]
            [gensql.structure-learning.bayesdb-import :as bayesdb-import]
            [gensql.inference.gpm :as gpm]))

(def bdb-export
  "A BayesDB model export built from a toy dataset.
  Notice that column names need not be keywordized."
  {"models" [{"clusters" [[[0 1 2 3 4 6 8 10 13 15 18 19 20 25 27 31 36 44]
                           [5 7 11 12 14 16 21 22 24 28 32 34 35 37 38 39 40 41 42 43 45 46 47 48 49]
                           [9 17 23 26 29 33]
                           [30]]],
              "cluster-crp-hyperparameters" [0.38895897054520057],
              "column-partition" [["height" "gender" "age"]],
              "column-hypers" {"gender" {"alpha" 1.1444192979749988},
                               "age" {"s" 137.58727727093182,
                                      "r" 22.608918839237138,
                                      "m" 45.15678042233793,
                                      "nu" 38.88720375758538},
                               "height" {"s" 28.396784120505796,
                                         "r" 0.025715400012656844,
                                         "m" 163.73748175906897,
                                         "nu" 51.0}}}
             {"clusters" [[[0 1 2 3 4 6 8 9 10 13 15 17 18 19 20 23 25 26 27 29 30 31 33 36 44]
                           [5 7 11 12 14 16 21 22 24 28 32 34 35 37 38 39 40 41 42 43 45 46 47 48 49]]
                          [[27 42]
                           [16 25 32 48]
                           [6 35 38 39 43 47 49]
                           [11 20 33]
                           [1 4 21 23 24 29 41 45]
                           [10 37 44 46]
                           [2 3 5 7 13 15 17 28 30 36]
                           [12 18 31 34]
                           [40]
                           [0]
                           [22]
                           [8 19]
                           [14]
                           [9 26]]],
              "cluster-crp-hyperparameters" [0.29698426982540743 5.775734792970424],
              "column-partition" [["height" "gender"] ["age"]],
              "column-hypers" {"gender" {"alpha" 1.0},
                               "age" {"s" 28.114030006503604,
                                      "r" 0.22506137492042433,
                                      "m" 45.15678042233793,
                                      "nu" 25.8917571570077},
                               "height" {"s" 33.28393591020709,
                                         "r" 0.0196078431372549,
                                         "m" 172.80585596103447,
                                         "nu" 44.53366582302489}}}],
   "column-statistical-types" {"gender" "nominal", "age" "numerical", "height" "numerical"},
   "categories" {"gender" ["female" "male"]}})

(def data
  "A toy dataset used to build a Bayes DB model export.
  Notice that column names are keywordized and column values
  for numerical columns are actual numbers and not strings."
  [{:age 48.24869, :height 161.11601, :gender "female"}
   {:age 43.776485, :height 160.43707, :gender "female"}
   {:age 43.943657, :height 161.27774, :gender "female"}
   {:age 42.85406, :height 159.994, :gender "female"}
   {:age 46.730816, :height 160.0419, :gender "female"}
   {:age 40.396923, :height 176.11424, :gender "female"}
   {:age 48.489624, :height 161.18274, :gender "female"}
   {:age 43.477585, :height 175.8591, :gender "male"}
   {:age 45.638077, :height 160.69887, :gender "female"}
   {:age 44.50126, :height 162.24196, :gender "female"}
   {:age 47.924217, :height 162.04704, :gender "female"}
   {:age 40.87972, :height 176.33559, :gender "female"}
   {:age 44.355167, :height 175.543, :gender "male"}
   {:age 44.23189, :height 161.56635, :gender "female"}
   {:age 47.26754, :height 176.50114, :gender "male"}
   {:age 42.800217, :height 161.27985, :gender "female"}
   {:age 44.655144, :height 176.60793, :gender "male"}
   {:age 43.24428, :height 161.29745, :gender "female"}
   {:age 45.084427, :height 160.48422, :gender "female"}
   {:age 46.16563, :height 161.63524, :gender "female"}
   {:age 42.798763, :height 160.06999, :gender "female"}
   {:age 47.289448, :height 176.23465, :gender "male"}
   {:age 46.80318, :height 176.20517, :gender "male"}
   {:age 46.00499, :height 161.61508, :gender "female"}
   {:age 46.801712, :height 176.87424, :gender "male"}
   {:age 43.632545, :height 162.14302, :gender "female"}
   {:age 44.75422, :height 160.5407, :gender "female"}
   {:age 43.12846, :height 160.6665, :gender "female"}
   {:age 44.464222, :height 175.42235, :gender "male"}
   {:age 46.06071, :height 162.69423, :gender "female"}
   {:age 43.61668, :height 157.9667, :gender "female"}
   {:age 44.206493, :height 161.17851, :gender "male"}
   {:age 43.625656, :height 175.88077, :gender "female"}
   {:age 43.30959, :height 162.79837, :gender "female"}
   {:age 43.65751, :height 176.37244, :gender "male"}
   {:age 44.97467, :height 175.96977, :gender "male"}
   {:age 42.76538, :height 161.0654, :gender "female"}
   {:age 45.46883, :height 176.12625, :gender "male"}
   {:age 48.319603, :height 175.86026, :gender "male"}
   {:age 46.48409, :height 175.79822, :gender "male"}
   {:age 44.61633, :height 176.1954, :gender "female"}
   {:age 43.224743, :height 176.35046, :gender "male"}
   {:age 43.505684, :height 175.91644, :gender "male"}
   {:age 48.38491, :height 175.69824, :gender "male"}
   {:age 45.101616, :height 161.34514, :gender "female"}
   {:age 43.72601, :height 176.35405, :gender "male"}
   {:age 45.381832, :height 175.4414, :gender "male"}
   {:age 49.200512, :height 176.45265, :gender "male"}
   {:age 45.24032, :height 176.06401, :gender "male"}
   {:age 46.234406, :height 176.12007, :gender "male"}])

(deftest smoke
  (let [models (bayesdb-import/xcat-gpms bdb-export data)
        model (first models)
        targets (set (keys (get-in model [:latents :z])))
        row (gpm/simulate model targets {})]

    (is (= (count models) 2))
    (is (every? gpm/gpm? models))

    ;; Notice that targets (column names) in the returned XCat models are keywords.
    (is (= targets #{:age :height :gender}))

    ;; Checking simulated data.
    (is (map? row))
    (is (= #{:age :height :gender} (set (keys row))))
    (is (number? (:age row)))
    (is (number? (:height row)))
    (is (#{"male" "female"} (:gender row)))))
