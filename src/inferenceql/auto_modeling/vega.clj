(ns inferenceql.auto-modeling.vega
  (:require [clojure.data.json :as json]
            [clojure.edn :as edn]
            [inferenceql.auto-modeling.dvc :as dvc]))

(def vega-lite-5-schema "https://vega.github.io/schema/vega-lite/v5.json")

(def obs-data-color "#4e79a7") ;; Tableau-10 Blue
(def virtual-data-color "#f28e2b") ;; Tableau-10 Orange
(def splom-obs-data-color "rgb(31,119,180)") ;; Tableau-10 (old) Blue
(def splom-virtual-data-color "rgb(255,127,14)") ;; Tableau-10 (old) Orange
(def unselected-color "lightgrey")

(def strip-plot-quant-size
  "Size of the strip plot for the quantitative dimension"
  400)
(def strip-plot-step-size
  "Width of each band in the strip plot in the categorical dimension"
  40)

(def scatter-plot-width
  "A general width setting vega-lite plots"
  400)
(def scatter-plot-height
  "A general height setting vega-lite plots"
  400)

(defn vega-type-fn
  "Given a `schema`, returns a vega-type function.

  Args:
    schema: (map) Mapping from column name to iql stat-type.

  Returns: (a function) Which returns a vega-lite type given `col-name`, a column name
    from the data table. Returns nil if vega-lite type can't be deterimend."
  [schema]
  (fn [col-name]
    ;; Mapping from multi-mix stat-types to vega-lite data-types.
    (let [mapping {:gaussian "quantitative"
                   :categorical "nominal"}]
      (get mapping (get schema col-name)))))

(defn should-bin?
  "Returns whether data for a certain column should be binned in a vega-lite spec.

  Args:
    col-type: A vega-lite column type."
  [col-type]
  (case col-type
    "quantitative" true
    "nominal" false
    false))

(defn histogram
  "Generates a vega-lite spec for a histogram.
  `selections` is a collection of maps representing data in selected rows and columns.
  `col` is the key within each map in `selections` that is used to extract data for the histogram.
  `vega-type` is a function that takes a column name and returns an vega datatype."
  [col vega-type]
  (let [col-type (vega-type col)
        bin-flag (should-bin? col-type)

        scale (if (= col-type "numerical")
                {:x "shared" :y "shared"}
                {:y "shared"})]
    {:resolve {:scale scale}
     :spacing -1
     :hconcat [{:title {:text "Observed" :anchor "middle" :orient "bottom"
                        :fontWeight "normal" :fontStyle "italic"}
                :layer [{:mark {:type "bar"
                                :color unselected-color
                                :tooltip {:content "data"}}
                         :params [{:name "brush-all"
                                   :select {:type "interval" :encodings ["x"]}}]
                         :transform [{:filter {:field "collection" :equal "observed"}}]
                         :encoding {:x {:bin bin-flag
                                        :field col
                                        :type col-type}
                                    :y {:aggregate "count"
                                        :type "quantitative"}}}
                        {:mark {:type  "bar",
                                :color obs-data-color}
                         :transform [{:filter {:param "brush-all"}}
                                     {:filter {:field "collection" :equal "observed"}}],
                         :encoding {:x {:bin bin-flag
                                        :field col
                                        :type col-type}
                                    :y {:aggregate "count",
                                        :type "quantitative"}}}]}
               {:title {:text "Virtual" :anchor "middle" :orient "bottom"
                        :fontWeight "normal" :fontStyle "italic"}
                :layer [{:mark {:type "bar"
                                :color unselected-color
                                :tooltip {:content "data"}}
                         :params [{:name "brush-all"
                                   :select {:type "interval" :encodings ["x"]}}]
                         :transform [{:filter {:field "collection" :equal "virtual"}}]
                         :encoding {:x {:bin bin-flag
                                        :field col
                                        :type col-type}
                                    :y {:aggregate "count"
                                        :type "quantitative"
                                        :axis {:labels false :title nil}}}}
                        {:mark {:type "bar",
                                :color virtual-data-color}
                         :transform [{:filter {:param "brush-all"}}
                                     {:filter {:field "collection" :equal "virtual"}}]
                         :encoding {:x {:bin bin-flag
                                        :field col
                                        :type col-type}
                                    :y {:aggregate "count",
                                        :type "quantitative"
                                        :axis {:labels false :title nil}}}}]}]}))

(defn- scatter-plot
  "Generates vega-lite spec for a scatter plot.
  Useful for comparing quatitative-quantitative data."
  [cols-to-draw]
  (let [zoom-control-name (gensym "zoom-control")] ; Random id so pan/zoom is independent.
    {:width scatter-plot-width
     :height scatter-plot-height
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
     :encoding {:x {:field (first cols-to-draw)
                    :type "quantitative"
                    :scale {:zero false}}
                :y {:field (second cols-to-draw)
                    :type "quantitative"
                    :scale {:zero false}
                    :axis {:minExtent 40}}
                :opacity {:field "collection"
                          :scale {:domain ["observed", "virtual"]
                                  :range [{:expr "splomAlphaObserved"} {:expr "splomAlphaVirtual"}]}
                          :legend nil}
                :color {:condition {:param "brush-all"
                                    :field "collection"
                                    :scale {:domain ["observed", "virtual"]
                                            :range [obs-data-color virtual-data-color]}
                                    :legend {:orient "top"
                                             :title nil}}
                        :value unselected-color}}}))

(defn- strip-plot-size-helper
  "Returns a vega-lite height/width size.

  Args:
    `col-type` - A vega-lite column type."
  [col-type]
  (case col-type
    "quantitative" strip-plot-quant-size
    "nominal" {:step strip-plot-step-size}))

(defn- strip-plot
  "Generates vega-lite spec for a strip plot.
  Useful for comparing quantitative-nominal data."
  [cols-to-draw vega-type]
  (let [zoom-control-name (gensym "zoom-control") ; Random id so pan/zoom is independent.

        ;; NOTE: This is a temporary hack to that forces the x-channel in the plot to be "numerical"
        ;; and the y-channel to be "nominal". The rest of the code remains nuetral to the order so that
        ;; it can be used by the iql-viz query language later regardless of column type order.
        first-col-nominal (= "nominal" (vega-type (first cols-to-draw)))
        cols-to-draw (cond->> (take 2 cols-to-draw)
                              first-col-nominal (reverse))

        [x-field y-field] cols-to-draw
        [x-type y-type] (map vega-type cols-to-draw)
        quant-dimension (if (= x-type "quantitative") :x :y)
        [width height] (map (comp strip-plot-size-helper vega-type) cols-to-draw)]
    {:resolve {:scale {:x "shared"}}
     :spacing -1
     :vconcat [{:width width
                :height height
                :title {:text "Observed" :anchor "middle" :angle -90 :orient "left"
                        :fontWeight "normal" :fontStyle "italic"}
                :transform [{:filter {:field "collection" :equal "observed"}}]
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
                          :select  {:type "interval"
                                    :on "[mousedown[!event.shiftKey], window:mouseup] > window:mousemove"
                                    :translate "[mousedown[!event.shiftKey], window:mouseup] > window:mousemove"
                                    :clear "dblclick[!event.shiftKey]"
                                    :zoom "wheel![!event.shiftKey]"}}]
                :encoding {:x {:field x-field
                               :type x-type
                               :axis {:grid true :gridDash [2 2]
                                      :labels false :title nil}
                               ;; Note: this assumes the x-axis is quantitative.
                               :scale {:zero false}}
                           :y {:field y-field
                               :type y-type
                               :axis {:grid true :gridDash [2 2]
                                      :minExtent 70}}
                           :color {:condition {:param "brush-all"
                                               :value obs-data-color}}}}
               {:width width
                :height height
                :title {:text "Virtual" :anchor "middle" :angle -90 :orient "left"
                        :fontWeight "normal" :fontStyle "italic"}
                :transform [{:filter {:field "collection" :equal "virtual"}}]
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
                          :select {:type "interval"
                                   :on "[mousedown[!event.shiftKey], window:mouseup] > window:mousemove"
                                   :translate "[mousedown[!event.shiftKey], window:mouseup] > window:mousemove"
                                   :clear "dblclick[!event.shiftKey]"
                                   :zoom "wheel![!event.shiftKey]"}}]
                :encoding {:x {:field x-field
                               :type x-type
                               :axis {:grid true :gridDash [2 2]}
                               ;; Note: this assumes the x-axis is quantitative.
                               :scale {:zero false}}
                           :y {:field y-field
                               :type y-type
                               :axis {:grid true :gridDash [2 2]
                                      :minExtent 70}}
                           :color {:condition {:param "brush-all"
                                               :value virtual-data-color}}}}]}))

(defn- table-bubble-plot
  "Generates vega-lite spec for a table-bubble plot.
  Useful for comparing nominal-nominal data."
  [cols-to-draw]
  (let [[x-field y-field] cols-to-draw]
    {:spacing -1
     :vconcat [{:title {:text "Observed" :anchor "middle" :angle -90 :orient "left"
                        :fontWeight "normal" :fontStyle "italic"}
                :layer [{:mark {:type "circle"
                                :tooltip {:content "data"}
                                :color unselected-color}
                         :params [{:name "brush-all"
                                   :select {:type "interval"}}]
                         :transform [{:filter {:field "collection" :equal "observed"}}]
                         :encoding {:x {:field x-field
                                        :type "nominal"
                                        :axis {:labels false :title nil}}
                                    :y {:field y-field
                                        :type "nominal"}
                                    :size {:aggregate "count"
                                           :type "quantitative"
                                           :legend nil}}}
                        {:mark {:type  "circle"
                                :color obs-data-color}
                         :transform [{:filter {:param "brush-all"}}
                                     {:filter {:field "collection" :equal "observed"}}],
                         :encoding {:x {:field x-field
                                        :type "nominal"
                                        :axis {:labels false :title nil}}
                                    :y {:field y-field
                                        :type "nominal"}
                                    :size {:aggregate "count"
                                           :type "quantitative"
                                           :legend nil}}}]}
               {:title {:text "Virtual" :anchor "middle" :angle -90 :orient "left"
                        :fontWeight "normal" :fontStyle "italic"}
                :layer [{:mark {:type "circle"
                                :tooltip {:content "data"}
                                :color unselected-color}
                         :params [{:name "brush-all"
                                   :select {:type "interval"}}]
                         :transform [{:filter {:field "collection" :equal "virtual"}}]
                         :encoding {:x {:field x-field
                                        :type "nominal"}
                                    :y {:field y-field
                                        :type "nominal"}
                                    :size {:aggregate "count"
                                           :type "quantitative"
                                           :legend nil}}}
                        {:mark {:type "circle"
                                :color virtual-data-color}
                         :transform [{:filter {:param "brush-all"}}
                                     {:filter {:field "collection" :equal "virtual"}}],
                         :encoding {:x {:field x-field
                                        :type "nominal"}
                                    :y {:field y-field
                                        :type "nominal"}
                                    :size {:aggregate "count"
                                           :type "quantitative"
                                           :legend nil}}}]}]}))

(defn histogram-section [title subtitle cols vega-type]
  (when (seq cols)
    (let [specs (for [col cols] (histogram col vega-type))]
      {:concat specs
       :columns 3
       :spacing {:column 150 :row 30}
       :title {:text title
               :subtitle subtitle
               :fontSize 20
               :subtitleFontSize 20
               :offset 40
               :frame "group"}})))

(defn scatter-plot-section [cols]
  (when (seq cols)
    (let [specs (for [col-pair cols] (scatter-plot col-pair))]
      {:concat specs
       :columns 3
       :spacing {:column 150 :row 30}
       :resolve {:legend {:color "shared"}}
       :title {:text "2-D marginals"
               :subtitle "numerical-numerical"
               :fontSize 20
               :subtitleFontSize 20
               :offset 40
               :frame "group"}})))

(defn bubble-plot-section  [cols data]
  (when (seq cols)
    (let [specs (for [col-pair cols]
                  (let [[col-1 col-2] col-pair
                        col-1-vals (count (distinct (map #(get % col-1) data)))
                        col-2-vals (count (distinct (map #(get % col-2) data)))
                        col-pair (if (>= col-1-vals col-2-vals)
                                   [col-1 col-2]
                                   [col-2 col-1])]
                    ;; Produce the bubble plot with the more optionful column on the x-dim.
                    (table-bubble-plot col-pair)))]
      {:concat specs
       :columns 3
       :spacing {:column 150 :row 30}
       :title {:text "2-D marginals"
               :subtitle "nominal-nominal"
               :fontSize 20
               :subtitleFontSize 20
               :offset 40
               :frame "group"}})))

(defn strip-plot-section [cols vega-type]
  (when (seq cols)
    (let [specs (for [col-pair cols]
                  (strip-plot col-pair vega-type))]
      {:concat specs
       :columns 3
       :spacing {:column 150 :row 80}
       :title {:text "2-D marginals"
               :subtitle "nominal-numerical"
               :fontSize 20
               :subtitleFontSize 20
               :offset 40
               :frame "group"}})))

(defn generate-spec [data num-observed num-virtual sections]
  {:$schema vega-lite-5-schema
   :vconcat sections
   :spacing 100
   :data {:values data}
   :params [{:name "splomAlphaObserved"
             :value 0.7
             :bind {:input "range" :min 0 :max 1 :step 0.05
                    :name "scatter plots - alpha (observed data)"
                    :element "#controls"}}
            {:name "splomAlphaVirtual"
             :value 0.7
             :bind {:input "range" :min 0 :max 1 :step 0.05
                    :name "scatter plots - alpha (virtual data)"
                    :element "#controls"}}
            {:name "splomPointSize"
             :value 30
             :bind {:input "range" :min 1 :max 100 :step 1
                    :name "scatter plots - point size"
                    :element "#controls"}}
            {:name "numObservedPoints"
             :value num-observed
             :bind {:input "range" :min 1 :max num-observed :step 1
                    :name "number of points (observed data)"
                    :element "#controls"}}
            {:name "numVirtualPoints"
             :value num-virtual
             :bind {:input "range" :min 1 :max num-virtual :step 1
                    :name "number of points (virtual data)"
                    :element "#controls"}}]
   :transform [{:window [{:op "row_number", :as "row_number"}]
                :groupby ["collection"]}
               ;; FIXME: Scatter plot points do not always get updated
               ;; based on this filter. It could be a bug in vega-lite.
               {:filter {:or [{:and [{:field "collection" :equal "observed"}
                                     {:field "row_number" :lte {:expr "numObservedPoints"}}]}
                              {:and [{:field "collection" :equal "virtual"}
                                     {:field "row_number" :lte {:expr "numVirtualPoints"}}]}]}}]
   :config {:countTitle "Count"
            :axisY {:minExtent 10
                    :labelLimit 50}}
   :resolve {:legend {:size "independent"
                      :color "independent"}
             :scale {:color "independent"}}})

(defn qc-dashboard-spec [{sample-path :samples schema-path :schema}]
  (let [schema (-> schema-path str slurp edn/read-string)
        samples (-> sample-path str slurp edn/read-string)

        num-observed (-> (group-by :collection samples)
                         (get "observed")
                         (count))
        num-virtual (-> (group-by :collection samples)
                        (get "virtual")
                        (count))

        ;; Visualize the columns set in params.yaml.
        ;; If not specified, visualize all the columns.
        cols (or (get-in (dvc/yaml) [:qc :columns])
                 (keys schema))
        ;; Either way we will visualize at most 8 columns.
        cols (take 8 cols)

        vega-type (vega-type-fn schema)
        ;; Only keep the columns that we can determine a vega-type for.
        cols (filter vega-type cols)
        cols-by-type (group-by vega-type cols)

        histograms-quant (histogram-section "1-D marginals" "(numerical columns)"
                                            (get cols-by-type "quantitative") vega-type)
        histograms-nom (histogram-section "1-D marginals" "(nominal columns)"
                                          (get cols-by-type "nominal") vega-type)

        select-pairs (for [x cols y cols :while (not= x y)] [x y])
        pair-types (group-by #(set (map vega-type %)) select-pairs)

        scatter-plots (scatter-plot-section (get pair-types #{"quantitative"}))
        bubble-plots (bubble-plot-section (get pair-types #{"nominal"}) samples)
        strip-plots (strip-plot-section (get pair-types #{"quantitative" "nominal"}) vega-type)
        sections (remove nil? [histograms-quant histograms-nom scatter-plots strip-plots bubble-plots])]
    (json/pprint (generate-spec samples num-observed num-virtual sections))))

(defn scatter-plot-for-splom [col-1 col-2]
  {:mark {:type "point"
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
   :encoding {:x {:field col-1
                  :type "quantitative"
                  :axis {:gridOpacity 0.4}}
              :y {:field col-2
                  :type "quantitative"
                  :axis {:gridOpacity 0.4}}
              :opacity {:field "collection"
                        :scale {:domain ["observed", "virtual"]
                                :range [{:expr "splomAlphaObserved"} {:expr "splomAlphaVirtual"}]}
                        :legend nil}
              :color {:condition {:param "brush-all"
                                  :field "collection"
                                  :scale {:domain ["observed", "virtual"]
                                          :range [splom-obs-data-color splom-virtual-data-color]}
                                  :legend {:orient "top"
                                           :title nil
                                           :offset 30}}
                      :value unselected-color}}})

(defn layered-histogram [col vega-type]
  (let [col-type (vega-type col)
        bin-flag (should-bin? col-type)]
    {:params [{:name "brush-all"
               :select {:type "interval" :encodings ["x"]}}]
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
                                :range [splom-obs-data-color splom-virtual-data-color]}
                        :legend {:orient "top"
                                 :offset 30
                                 :title nil}}}}))

(defn qc-splom-spec [{sample-path :samples schema-path :schema}]
  (let [schema (-> schema-path str slurp edn/read-string)
        samples (-> sample-path str slurp edn/read-string)

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
                                    (layered-histogram col-2 vega-type)
                                    ;; Each column has the same x-dimension.
                                    (scatter-plot-for-splom col-1 col-2)))]
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

        spec {:$schema vega-lite-5-schema
              :params [{:name "histAlphaObserved"
                        :value 0.6
                        :bind {:input "range" :min 0 :max 1 :step 0.05
                               :name "histograms - alpha (observed data)"
                               :element "#controls"}}
                       {:name "histAlphaVirtual"
                        :value 0.6
                        :bind {:input "range" :min 0 :max 1 :step 0.05
                               :name "histograms - alpha (virtual data)"
                               :element "#controls"}}
                       {:name "splomAlphaObserved"
                        :value 0.7
                        :bind {:input "range" :min 0 :max 1 :step 0.05
                               :name "scatter plots - alpha (observed data)"
                               :element "#controls"}}
                       {:name "splomAlphaVirtual"
                        :value 0.7
                        :bind {:input "range" :min 0 :max 1 :step 0.05
                               :name "scatter plots - alpha (virtual data)"
                               :element "#controls"}}
                       {:name "splomPointSize"
                        :value 30
                        :bind {:input "range" :min 1 :max 100 :step 1
                               :name "scatter plots - point size"
                               :element "#controls"}}
                       {:name "numObservedPoints"
                        :value num-obs-samples
                        :bind {:input "range" :min 1 :max num-obs-samples :step 1
                               :name "number of points (observed data)"
                               :element "#controls"}}
                       {:name "numVirtualPoints"
                        :value num-virtual-samples
                        :bind {:input "range" :min 1 :max num-virtual-samples :step 1
                               :name "number of points (virtual data)"
                               :element "#controls"}}]
              :data {:values samples}
              :transform [{:window [{:op "row_number", :as "row_number"}]
                           :groupby ["collection"]}
                          ;; FIXME: Scatter plot points do not always get updated
                          ;; based on this filter. It could be a bug in vega-lite.
                          {:filter {:or [{:and [{:field "collection" :equal "observed"}
                                                {:field "row_number" :lte {:expr "numObservedPoints"}}]}
                                         {:and [{:field "collection" :equal "virtual"}
                                                {:field "row_number" :lte {:expr "numVirtualPoints"}}]}]}}]
              :hconcat plot-rows
              :spacing 40
              :config {:countTitle "Count"}
              :resolve {:legend {:color "shared"}
                        :scale {:color "shared"
                                :opacity "independent"
                                :x "independent"}}}]
    (json/pprint spec)))
