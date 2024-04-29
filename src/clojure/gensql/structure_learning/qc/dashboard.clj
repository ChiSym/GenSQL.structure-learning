(ns gensql.structure-learning.qc.dashboard
  "Code related to producing a vega-lite spec for a dashboard."
  (:require [clojure.data.json :as json]
            [clojure.edn :as edn]
            [cheshire.core :as cheshire]
            [gensql.structure-learning.dvc :as dvc]
            [gensql.structure-learning.qc.vega :as vega]
            [gensql.structure-learning.qc.util :refer [filtering-summary should-bin? bind-to-element
                                                       obs-data-color synthetic-data-color
                                                       unselected-color vega-type-fn
                                                       vl5-schema bar-plots-1-d
                                                       most-frequent]]))

(defn histogram-quant
  "Generates a vega-lite spec for a histogram.
  `selections` is a collection of maps representing data in selected rows and columns.
  `col` is the key within each map in `selections` that is used to extract data for the histogram.
  `vega-type` is a function that takes a column name and returns an vega datatype."
  [col vega-type samples]
  (let [col-type (vega-type col)
        bin-flag (should-bin? col-type)
        fsum (filtering-summary [col] vega-type nil samples)]
    {:resolve {:scale {:x "shared" :y "shared"}}
     :spacing 0
     :bounds "flush"
     :transform [{:window [{:op "row_number", :as "row_number_subplot"}]
                  :groupby ["collection"]}
                 {:filter {:or [{:and [{:field "collection" :equal "observed"}
                                       {:field "row_number_subplot" :lte {:expr "numObservedPoints"}}]}
                                {:and [{:field "collection" :equal "synthetic"}
                                       {:field "row_number_subplot" :lte (:num-valid fsum)}
                                       {:field "row_number_subplot" :lte {:expr "numVirtualPoints"}}]}]}}]
     :facet {:field "collection"
             :type "nominal"
             :header {:title nil :labelOrient "bottom" :labelPadding 34}}
     :spec {:layer [{:mark {:type "bar"
                            :color unselected-color
                            :tooltip {:content "data"}}
                     :params [{:name "brush-all"
                               ;; TODO: is there a way to select based on collection here as well?
                               :select {:type "interval" :encodings ["x"]}}]
                     :encoding {:x {:bin bin-flag
                                    :field col
                                    :type col-type}
                                :y {:aggregate "count"
                                    :type "quantitative"}}}
                    {:transform [{:filter {:param "brush-all"}}]
                     :mark {:type "bar"}
                     :encoding {:x {:bin bin-flag
                                    :field col
                                    :type col-type}
                                :y {:aggregate "count"
                                    :type "quantitative"}
                                :color {:field "collection"
                                        :scale {:domain ["observed", "synthetic"]
                                                :range [obs-data-color synthetic-data-color]}
                                        :legend {:orient "top"
                                                 :title nil}}}}]}}))


(defn histogram-wih-point-indicators
  "Generates a vega-lite spec for showing histograms with points indicating frequencies.
  `col` is the key within each map in `selections` that is used to extract data for the histogram.
  `vega-type` is a function that takes a column name and returns an vega datatype.
  `samples` is a collection of maps representing data in selected rows and columns."
  [col vega-type samples]
  (let [col-type (vega-type col)
        bin-flag (should-bin? col-type)
        f-sum (filtering-summary [col] vega-type nil samples)]
    {:mark {:type "point"
            :color unselected-color
            :tooltip {:content "data"}}
     :transform [{:window [{:op "row_number", :as "row_number_subplot"}]
                  :groupby ["collection"]}
                 {:filter {:or [{:and [{:field "collection" :equal "observed"}
                                       {:field "row_number_subplot" :lte {:expr "numObservedPoints"}}]}
                                {:and [{:field "collection" :equal "synthetic"}
                                       {:field "row_number_subplot" :lte (:num-valid f-sum)}
                                       {:field "row_number_subplot" :lte {:expr "numVirtualPoints"}}]}]}}]
     :params [{:name "brush-all"
               :select {:type "point"
                        :nearest true
                        :toggle "true"
                        :on "click[!event.shiftKey]"
                        :fields [col "collection"]
                        :clear "dblclick[!event.shiftKey]"}}]
     :encoding {:y {:bin bin-flag
                    :field col
                    :type col-type
                    :axis {:titleAnchor "start" :titleAlign "right" :titlePadding 1}}
                :x {:aggregate "count"
                    :type "quantitative"
                    :axis {:orient "top"}}
                :color {:condition {:param "brush-all"
                                    :field "collection"
                                    :scale {:domain ["observed", "synthetic"]
                                            :range [obs-data-color synthetic-data-color]}
                                    :legend {:orient "top"
                                             :title nil
                                             :offset 10}}}}}))

(defn histogram-wih-barplots
  "Generates a vega-lite spec for showing histograms comparing two bar plots.
  `col` is the key within each map in `selections` that is used to extract data for the histogram.
  `vega-type` is a function that takes a column name and returns an vega datatype.
  `samples` is a collection of maps representing data in selected rows and columns."
  [col vega-type samples]
  (let [col-type (vega-type col)
        bin-flag (should-bin? col-type)
        f-sum (filtering-summary [col] vega-type nil samples)
        col-vals (map col samples)
        max-freq (most-frequent col-vals)
        col-domain (remove nil? (set col-vals))
        bar-plot-template (fn
                           [source color numPoints]
                           {:mark {:type "bar"
                                   :color unselected-color
                                   :tooltip {:content "data"}}
                            :transform [
                                        {:filter {:field col :oneOf col-domain}}
                                        {:window [{:op "row_number", :as "row_number_subplot"}]
                                         :groupby ["collection"]}
                                        {:filter {:and [{:field "collection" :equal source}
                                                        {:field "row_number_subplot" :lte (:num-valid f-sum)}
                                                        {:field "row_number_subplot" :lte {:expr numPoints}}]}}
                                        ]
                            :params [{:name "brush-all"
                                      :select {:type "point"
                                               :nearest true
                                               :toggle "true"
                                               :on "click[!event.shiftKey]"
                                               :fields [col "collection"]
                                               :clear "dblclick[!event.shiftKey]"}}]
                            :encoding {:y {:bin bin-flag
                                           :field col
                                           :type col-type
                                           :axis {:titleAnchor "start" :titleAlign "right" :titlePadding 1}}
                                       :x {:aggregate "count"
                                           :type "quantitative"
                                           ; Next, ensure a shared the scale.
                                           :scale {:domain [0, (* 1.1 (/ max-freq 2))]}
                                           :axis {:orient "top"}}
                                       :color {:value color}}})
        ]
    {:concat [
              (bar-plot-template "observed" obs-data-color "numObservedPoints")
              (bar-plot-template "synthetic" synthetic-data-color "numVirtualPoints")]}))

(defn histogram-nom
  "Generates a vega-lite spec for showing histograms comparing synthetic and observed data
  for univariate, nominal distributions.
  `col` is the key within each map in `selections` that is used to extract data for the histogram.
  `vega-type` is a function that takes a column name and returns an vega datatype.
  `samples` is a collection of maps representing data in selected rows and columns."
  [col vega-type samples]
  (if bar-plots-1-d
    (histogram-wih-barplots col vega-type samples)
    (histogram-wih-point-indicators col vega-type samples)))

(defn- scatter-plot
  "Generates vega-lite spec for a scatter plot.
  Useful for comparing quatitative-quantitative data."
  [col-1 col-2 vega-type correlation samples]
  (let [zoom-control-name (gensym "zoom-control") ; Random id so pan/zoom is independent.
        f-sum (filtering-summary [col-1 col-2] vega-type nil samples)

        base-spec {:width 400
                   :height 400
                   :layer [{:transform [{:window [{:op "row_number", :as "row_number_subplot"}]
                                         :groupby ["collection"]}
                                        {:filter {:or [{:and [{:field "collection" :equal "observed"}
                                                              {:field "row_number_subplot" :lte {:expr "numObservedPoints"}}]}
                                                       {:and [{:field "collection" :equal "synthetic"}
                                                              {:field "row_number_subplot" :lte (:num-valid f-sum)}
                                                              {:field "row_number_subplot" :lte {:expr "numVirtualPoints"}}]}]}}]
                            :mark {:type "point"
                                   :tooltip {:content "data"}
                                   :filled true
                                   :size {:expr "splomPointSize"}}
                            :params [{:name zoom-control-name
                                      :bind "scales"
                                      :select {:type "interval"
                                               :on "[mousedown[event.shiftKey], window:mouseup] > window:mousemove"
                                               :translate "[mousedown[event.shiftKey], window:mouseup] > window:mousemove"
                                               :clear "dblclick[event.shiftKey]"
                                               :zoom "wheel![event.shiftKey]"}}
                                     {:name :brush-all
                                      :select {:type "interval"
                                               :on "[mousedown[!event.shiftKey], window:mouseup] > window:mousemove"
                                               :translate "[mousedown[!event.shiftKey], window:mouseup] > window:mousemove"
                                               :clear "dblclick[!event.shiftKey]"
                                               :zoom "wheel![!event.shiftKey]"}}]
                            :encoding {:x {:field col-1
                                           :type "quantitative"
                                           :scale {:zero false}
                                           :axis {:title col-1}}
                                       :y {:field col-2
                                           :type "quantitative"
                                           :scale {:zero false}
                                           :axis {:minExtent 40
                                                  :title col-2}}
                                       :order {:condition {:param "brush-all"
                                                           :value 1}
                                               :value 0}
                                       :opacity {:field "collection"
                                                 :scale {:domain ["observed", "synthetic"]
                                                         :range [{:expr "splomAlphaObserved"} {:expr "splomAlphaVirtual"}]}
                                                 :legend nil}
                                       :color {:condition {:param "brush-all"
                                                           :field "collection"
                                                           :scale {:domain ["observed", "synthetic"]
                                                                   :range [obs-data-color synthetic-data-color]}
                                                           :legend {:orient "top"
                                                                    :title nil}}
                                               :value unselected-color}}}]}]
    (vega/regression-line col-1 col-2 correlation samples base-spec)))

(defn- strip-plot-size-helper
  "Returns a vega-lite height/width size.

  Args:
    `col-type` - A vega-lite column type."
  [col-type]
  (case col-type
    "quantitative" 400
    "nominal" {:step 24}))

(defn- strip-plot
  "Generates vega-lite spec for a strip plot.
  Useful for comparing quantitative-nominal data."
  [cols vega-type n-cats samples]
  (let [zoom-control-name (gensym "zoom-control") ; Random id so pan/zoom is independent.
        ;; NOTE: This is a temporary hack to that forces the x-channel in the plot to be "numerical"
        ;; and the y-channel to be "nominal". The rest of the code remains nuetral to the order so that
        ;; it can be used by the iql-viz query language later regardless of column type order.
        first-col-nominal (= "nominal" (vega-type (first cols)))
        cols-to-draw (cond->> (take 2 cols)
                              first-col-nominal (reverse))

        [x-field y-field] cols-to-draw
        [x-type y-type] (map vega-type cols-to-draw)
        quant-dimension (if (= x-type "quantitative") :x :y)
        [width height] (map (comp strip-plot-size-helper vega-type) cols-to-draw)

        f-sum (filtering-summary cols vega-type n-cats samples)
        y-cats (get-in f-sum [:top-cats y-field])]
    {:resolve {:scale {:x "shared" :y "shared"}}
     :spacing 0
     :bounds "flush"
     :transform [;; Filtering for top categories
                 {:filter {:field y-field :oneOf y-cats}}
                 {:window [{:op "row_number", :as "row_number_subplot"}]
                  :groupby ["collection"]}
                 ;; Displaying an equal number of synthetic data points as observed datapoints.
                 ;; Filtering synthetic and observed datapoints based on user-set limit.
                 {:filter {:or [{:and [{:field "collection" :equal "observed"}
                                       {:field "row_number_subplot" :lte {:expr "numObservedPoints"}}]}
                                {:and [{:field "collection" :equal "synthetic"}
                                       {:field "row_number_subplot" :lte (:num-valid f-sum)}
                                       {:field "row_number_subplot" :lte {:expr "numVirtualPoints"}}]}]}}]
     :width width
     :height height
     :mark {:type "tick"
            :tooltip {:content "data"}
            :color unselected-color}
     :params [{:name zoom-control-name
               :bind "scales"
               :select {:type "interval"
                        :on "[mousedown[event.shiftKey], window:mouseup] > window:mousemove"
                        :translate "[mousedown[event.shiftKey], window:mouseup] > window:mousemove"
                        :clear "dblclick[event.shiftKey]"
                        :encodings [quant-dimension]
                        :zoom "wheel![event.shiftKey]"}}
              {:name "brush-all"
               :select  {:type "point"
                         :nearest true
                         :toggle "true"
                         :on "click[!event.shiftKey]"
                         :resolve "union"
                         :fields [y-field "collection"]
                         :clear "dblclick[!event.shiftKey]"}}]
     :encoding {:y {:field y-field
                    :type y-type}
                :x {:field x-field
                    :type x-type
                    :axis {:grid true :gridDash [2 2]
                           :orient "top"}
                    :scale {:zero false}}
                :row {:field "collection"
                      :type "nominal"
                      :header {:title nil
                               :labelPadding 0}}
                :order {:condition {:param "brush-all"
                                    :value 1}
                        :value 0}
                :color {:condition {:param "brush-all"
                                    :field "collection"
                                    :scale {:domain ["observed", "synthetic"]
                                            :range [obs-data-color synthetic-data-color]}
                                    :legend {:orient "top"
                                             :title nil
                                             :offset 10}}}}}))


(defn- table-bubble-plot
  "Generates vega-lite spec for a table-bubble plot.
  Useful for comparing nominal-nominal data."
  [cols vega-type n-cats samples]
  (let [[x-field y-field] cols
        f-sum (filtering-summary cols vega-type n-cats samples)
        x-cats (get-in f-sum [:top-cats x-field])
        y-cats (get-in f-sum [:top-cats y-field])]
    {:spacing 0
     :bounds "flush"
     :transform [;; Filtering for top categories
                 {:filter {:field x-field :oneOf x-cats}}
                 {:filter {:field y-field :oneOf y-cats}}
                 {:window [{:op "row_number", :as "row_number_subplot"}]
                  :groupby ["collection"]}
                 ;; Displaying an equal number of synthetic data points as observed datapoints.
                 ;; Filtering synthetic and observed datapoints based on user-set limit.
                 {:filter {:or [{:and [{:field "collection" :equal "observed"}
                                       {:field "row_number_subplot" :lte {:expr "numObservedPoints"}}]}
                                {:and [{:field "collection" :equal "synthetic"}
                                       {:field "row_number_subplot" :lte (:num-valid f-sum)}
                                       {:field "row_number_subplot" :lte {:expr "numVirtualPoints"}}]}]}}]
     :width {:step 20}
     :height {:step 20}
     :mark {:type "circle"
            :tooltip {:content "data"}
            :color unselected-color}
     :params [{:name "brush-all"
               :select {:type "point"
                        :nearest true
                        :toggle "true"
                        :on "click[!event.shiftKey]"
                        :resolve "union"
                        :fields [y-field x-field "collection"]
                        :clear "dblclick[!event.shiftKey]"}}]
     :encoding {:y {:field y-field
                    :type "nominal"
                    :axis {:titleOrient "left"
                           :titleAnchor "center"}}
                :x {:field x-field
                    :type "nominal"
                    :axis {:orient "top"
                           :labelAngle 315}}
                :column {:field "collection"
                         :type "nominal"
                         :header {:title nil
                                  :labelPadding 0}}
                :size {:aggregate "count"
                       :type "quantitative"
                       :legend nil}
                :color {:condition {:param "brush-all"
                                    :field "collection"
                                    :scale {:domain ["observed", "synthetic"]
                                            :range [obs-data-color synthetic-data-color]}
                                    :legend {:orient "top"
                                             :title nil
                                             :offset 10}}}}}))

(defn histogram-quant-section [title subtitle cols vega-type samples]
  (when (seq cols)
    (let [specs (for [col cols] (histogram-quant col vega-type samples))]
      {:concat specs
       :columns 3
       :spacing {:column 50 :row 50}
       :title {:text title
               :subtitle subtitle
               :fontSize 20
               :subtitleFontSize 20
               :offset 40
               :frame "group"}})))

(defn histogram-nom-section [title subtitle cols vega-type samples]
  (when (seq cols)
    (let [specs (for [col cols] (histogram-nom col vega-type samples))]
      {:concat specs
       :columns 3
       :spacing {:column 100 :row 50}
       :title {:text title
               :subtitle subtitle
               :fontSize 20
               :subtitleFontSize 20
               :offset 40
               :frame "group"}})))

(defn scatter-plot-section [cols vega-type correlation samples]
  (when (seq cols)
    (let [specs (for [[col-1 col-2] cols] (scatter-plot col-1 col-2 vega-type correlation samples))]
      {:concat specs
       :columns 3
       :spacing {:column 50 :row 50}
       :resolve {:legend {:color "shared"}}
       :title {:text "2-D marginals"
               :subtitle "numerical-numerical"
               :fontSize 20
               :subtitleFontSize 20
               :offset 40
               :frame "group"}})))

(defn bubble-plot-section [cols vega-type n-cats samples]
  (when (seq cols)
    (let [specs (for [col-pair cols]
                  (let [[col-1 col-2] col-pair
                        col-1-vals (count (distinct (map #(get % col-1) samples)))
                        col-2-vals (count (distinct (map #(get % col-2) samples)))
                        col-pair (if (>= col-1-vals col-2-vals)
                                   [col-2 col-1]
                                   [col-1 col-2])]
                    ;; Produce the bubble plot with the more optionful column on the x-dim.
                    (table-bubble-plot col-pair vega-type n-cats samples)))]
      {:concat specs
       :columns 3
       :spacing {:column 50 :row 50}
       :title {:text "2-D marginals"
               :subtitle "nominal-nominal"
               :fontSize 20
               :subtitleFontSize 20
               :offset 40
               :frame "group"}})))

(defn strip-plot-section [cols vega-type n-cats samples]
  (when (seq cols)
    (let [specs (for [col-pair cols]
                  (strip-plot col-pair vega-type n-cats samples))]
      {:concat specs
       :columns 3
       :spacing {:column 100 :row 50}
       :title {:text "2-D marginals"
               :subtitle "nominal-numerical"
               :fontSize 20
               :subtitleFontSize 20
               :offset 40
               :frame "group"}})))

(defn top-level-spec [data num-observed num-synthetic sections]
  (let [spec {:$schema vl5-schema
              :vconcat sections
              :spacing 100
              :data {:values data}
              :params [{:name "splomAlphaObserved"
                        :value 0.7
                        :bind {:input "range" :min 0 :max 1 :step 0.05
                               :name "scatter plots - alpha (observed data)"}}
                       {:name "splomAlphaVirtual"
                        :value 0.7
                        :bind {:input "range" :min 0 :max 1 :step 0.05
                               :name "scatter plots - alpha (synthetic data)"}}
                       {:name "splomPointSize"
                        :value 30
                        :bind {:input "range" :min 1 :max 100 :step 1
                               :name "scatter plots - point size"}}
                       {:name "numObservedPoints"
                        :value num-observed
                        :bind {:input "range" :min 1 :max num-observed :step 1
                               :name "number of points (observed data)"}}
                       {:name "numVirtualPoints"
                        :value num-synthetic
                        :bind {:input "range" :min 1 :max num-synthetic :step 1
                               :name "number of points (synthetic data)"}}
                       {:name "showRegression"
                        :value false
                        :bind {:input "checkbox"
                               :name "regression lines"}}]
              :transform [{:window [{:op "row_number", :as "row_number"}]
                           :groupby ["collection"]}]
              :config {:countTitle "Count"
                       :axisY {:minExtent 10}}
              :resolve {:legend {:size "independent"
                                 :color "independent"}
                        :scale {:color "independent"}}}]
    (update spec :params bind-to-element "#controls")))

(defn spec
  "Produces a vega-lite spec for the QC Dashboard app.
  Paths to samples and schema are required.
  Path to correlation data is optional."
  [{sample-path :samples schema-path :schema correlation-path :correlation}]
  (let [schema (-> schema-path str slurp edn/read-string)
        samples (-> sample-path str slurp edn/read-string)
        correlation (some-> correlation-path str slurp (cheshire/parse-string true))

        num-observed (-> (group-by :collection samples)
                         (get "observed")
                         (count))
        num-synthetic (-> (group-by :collection samples)
                        (get "synthetic")
                        (count))

        vega-type (vega-type-fn schema)

        ;; Visualize the columns set in params.yaml.
        ;; If not specified, visualize all the columns.
        cols (->> (or (get-in (dvc/yaml) [:qc :columns])
                      (keys schema))
                  (map keyword)
                  (take 8) ; Either way we will visualize at most 8 columns.
                  (filter vega-type)) ; Only keep the columns that we can determine a vega-type for.

        cols-by-type (group-by vega-type cols)

        histograms-quant (histogram-quant-section "1-D marginals" "(numerical columns)"
                                                  (get cols-by-type "quantitative")
                                                  vega-type
                                                  samples)
        histograms-nom (histogram-nom-section "1-D marginals" "(nominal columns)"
                                              (get cols-by-type "nominal")
                                              vega-type
                                              samples)

        select-pairs (for [x cols y cols :while (not= x y)] [x y])
        pair-types (group-by #(set (map vega-type %)) select-pairs)

        scatter-plots (scatter-plot-section (get pair-types #{"quantitative"})
                                            vega-type
                                            correlation
                                            samples)

        category-limit (get-in (dvc/yaml) [:qc :category_limit])
        bubble-plots (bubble-plot-section (get pair-types #{"nominal"})
                                          vega-type
                                          category-limit
                                          samples)
        strip-plots (strip-plot-section (get pair-types #{"quantitative" "nominal"})
                                        vega-type
                                        category-limit
                                        samples)
        sections (remove nil? [histograms-quant histograms-nom scatter-plots strip-plots bubble-plots])]
    (json/pprint (top-level-spec samples num-observed num-synthetic sections))))
