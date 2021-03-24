(ns inferenceql.auto-modeling.qc.splom
  "Code related to producing a vega-lite spec for a scatter plot matrix."
  (:require [clojure.data.json :as json]
            [clojure.edn :as edn]
            [cheshire.core :as cheshire]
            [inferenceql.auto-modeling.dvc :as dvc]
            [inferenceql.auto-modeling.qc.util :refer [filtering-summary should-bin? bind-to-element
                                                       obs-data-color virtual-data-color
                                                       unselected-color vega-type-fn
                                                       regression-color
                                                       vl5-schema]]))

(defn scatter-plot-for-splom [col-1 col-2 vega-type correlation samples]
  (let [f-sum (filtering-summary [col-1 col-2] vega-type nil samples)
        {:keys [slope intercept r-value p-value]} (get-in correlation [col-1 col-2])
        r-info-string (str (format "R²: %.2f" (* r-value r-value))
                           "   "
                           (format "p-value: %.2f" p-value))
        ;; Function y(x) for regression line.
        y (fn [x] (+ (* slope x) intercept))
        x-vals (->> samples
                    (filter (comp #{"observed"} :collection))
                    (map col-1)
                    (filter some?))
        [min-x max-x] [(apply min x-vals) (apply max x-vals)]]
    {:layer [{:mark {:type "point"
                     :tooltip {:content "data"}
                     :filled true
                     :size {:expr "splomPointSize"}}
              :params [{:name "zoom-control-splom"
                        :bind "scales"
                        :select {:type "interval"
                                 :resolve "global"
                                 :on "[mousedown[event.shiftKey], window:mouseup] > window:mousemove!",
                                 :translate "[mousedown[event.shiftKey], window:mouseup] > window:mousemove!",
                                 :clear "dblclick[event.shiftKey]"
                                 :zoom "wheel![event.shiftKey]"}}
                       {:name "brush-all"
                        :select {:type "interval"
                                 :resolve "global"
                                 :on "[mousedown[!event.shiftKey], window:mouseup] > window:mousemove"
                                 :translate "[mousedown[!event.shiftKey], window:mouseup] > window:mousemove!",
                                 :clear "dblclick[!event.shiftKey]"
                                 :zoom "wheel![!event.shiftKey]"}}]
              :transform [{:window [{:op "row_number", :as "row_number_subplot"}]
                           :groupby ["collection"]}
                          {:filter {:or [{:and [{:field "collection" :equal "observed"}
                                                {:field "row_number_subplot" :lte {:expr "numObservedPoints"}}]}
                                         {:and [{:field "collection" :equal "virtual"}
                                                {:field "row_number_subplot" :lte (:num-valid f-sum)}
                                                {:field "row_number_subplot" :lte {:expr "numVirtualPoints"}}]}]}}]
              :encoding {:x {:field col-1
                             :type "quantitative"
                             :axis {:gridOpacity 0.4
                                    :title col-1}}
                         :y {:field col-2
                             :type "quantitative"
                             :axis {:gridOpacity 0.4
                                    :title col-2}}
                         :opacity {:field "collection"
                                   :scale {:domain ["observed", "virtual"]
                                           :range [{:expr "splomAlphaObserved"} {:expr "splomAlphaVirtual"}]}
                                   :legend nil}
                         :color {:condition {:param "brush-all"
                                             :field "collection"
                                             :scale {:domain ["observed", "virtual"]
                                                     :range [obs-data-color virtual-data-color]}
                                             :legend {:orient "top"
                                                      :title nil
                                                      :offset 30}}
                                 :value unselected-color}}}
             {:data {:values [{:x min-x :y (y min-x)} {:x max-x :y (y max-x)}]}
              :mark {:type "line"
                     :strokeDash [4 4]
                     :color regression-color}
              :encoding {:x {:field "x"
                             :type "quantitative"}
                         :y {:field "y"
                             :type "quantitative"}
                         :opacity {:condition {:param "showRegression"
                                               :value 1}
                                   :value 0}}}
             {:data {:values [{:r-info-string r-info-string}]}
              :mark {:type "text"
                     :color regression-color
                     :x "width"
                     :align "right"
                     :y -5
                     :clip false}
              :encoding {:text {:field "r-info-string" :type "nominal"}
                         :opacity {:condition {:param "showRegression"
                                               :value 1}
                                   :value 0}}}]}))


(defn layered-histogram [col vega-type samples]
  (let [col-type (vega-type col)
        bin-flag (should-bin? col-type)
        f-sum (filtering-summary [col] vega-type nil samples)]
    {:params [{:name "brush-all"
               :select {:type "interval" :encodings ["x"]}}]
     :transform [{:window [{:op "row_number", :as "row_number_subplot"}]
                  :groupby ["collection"]}
                 {:filter {:or [{:and [{:field "collection" :equal "observed"}
                                       {:field "row_number_subplot" :lte {:expr "numObservedPoints"}}]}
                                {:and [{:field "collection" :equal "virtual"}
                                       {:field "row_number_subplot" :lte (:num-valid f-sum)}
                                       {:field "row_number_subplot" :lte {:expr "numVirtualPoints"}}]}]}}]
     :mark {:type "bar"
            :tooltip {:content "data"}}
     :encoding {:x {:bin bin-flag
                    :field col
                    :type col-type}
                :y {:aggregate "count"
                    :type "quantitative"
                    :stack nil}
                :opacity {:field "collection"
                          :scale {:domain ["observed", "virtual"]
                                  :range [{:expr "histAlphaObserved"} {:expr "histAlphaVirtual"}]}
                          :legend nil}
                :color {:field "collection"
                        :scale {:domain ["observed" "virtual"]
                                :range [obs-data-color virtual-data-color]}
                        :legend {:orient "top"
                                 :offset 30
                                 :title nil}}}}))

(defn spec [{sample-path :samples schema-path :schema correlation-path :correlation}]
  (let [schema (-> schema-path str slurp edn/read-string)
        samples (-> sample-path str slurp edn/read-string)
        correlation (-> correlation-path str slurp (cheshire/parse-string true))

        ;; Visualize the columns set in params.yaml.
        ;; If not specified, visualize all the columns.
        cols (or (get-in (dvc/yaml) [:qc :columns])
                 (keys schema))

        vega-type (vega-type-fn schema)
        cols (->> cols
                  ;; Get just the quantitative columns.
                  (filter (comp #{"quantitative"} vega-type))
                  ;; We will visualize at most 8 columns.
                  (take 8))

        plot-rows (for [col-1 cols]
                    (let [specs (for [col-2 cols]
                                  (if (= col-1 col-2)
                                    (layered-histogram col-2 vega-type samples)
                                    ;; Each column has the same x-dimension.
                                    (scatter-plot-for-splom col-1 col-2 vega-type
                                                            correlation samples)))]
                      {:vconcat specs
                       :spacing 80
                       :bounds "flush"
                       :resolve {:legend {:color "shared"}
                                 :scale {:color "shared"
                                         :opacity "independent"
                                         :x "shared"}}}))

        num-obs-samples (-> (group-by :collection samples)
                            (get "observed")
                            (count))
        num-virtual-samples (-> (group-by :collection samples)
                                (get "virtual")
                                (count))

        spec {:$schema vl5-schema
              :params [{:name "histAlphaObserved"
                        :value 0.7
                        :bind {:input "range" :min 0 :max 1 :step 0.05
                               :name "histograms - alpha (observed data)"}}
                       {:name "histAlphaVirtual"
                        :value 0.7
                        :bind {:input "range" :min 0 :max 1 :step 0.05
                               :name "histograms - alpha (virtual data)"}}
                       {:name "splomAlphaObserved"
                        :value 0.7
                        :bind {:input "range" :min 0 :max 1 :step 0.05
                               :name "scatter plots - alpha (observed data)"}}
                       {:name "splomAlphaVirtual"
                        :value 0.7
                        :bind {:input "range" :min 0 :max 1 :step 0.05
                               :name "scatter plots - alpha (virtual data)"}}
                       {:name "splomPointSize"
                        :value 30
                        :bind {:input "range" :min 1 :max 100 :step 1
                               :name "scatter plots - point size"}}
                       {:name "numObservedPoints"
                        :value num-obs-samples
                        :bind {:input "range" :min 1 :max num-obs-samples :step 1
                               :name "number of points (observed data)"}}
                       {:name "numVirtualPoints"
                        :value num-virtual-samples
                        :bind {:input "range" :min 1 :max num-virtual-samples :step 1
                               :name "number of points (virtual data)"}}
                       {:name "showRegression"
                        :value false
                        :bind {:input "checkbox"
                               :name "regression lines"}}]
              :data {:values samples}
              :transform [{:window [{:op "row_number", :as "row_number"}]
                           :groupby ["collection"]}]
              :hconcat plot-rows
              :spacing 40
              :config {:countTitle "Count"}
              :resolve {:legend {:color "shared"}
                        :scale {:color "shared"
                                :opacity "independent"
                                :x "independent"}}}]
    (-> spec
        (update :params bind-to-element "#controls")
        (json/pprint))))
