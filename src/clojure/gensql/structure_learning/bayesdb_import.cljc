(ns ^:deprecated gensql.structure-learning.bayesdb-import
  "Functions for importing BayesDB model dumps into GenSQL."
  (:require [clojure.walk :as walk]
            [medley.core :as medley]
            [gensql.inference.gpm.crosscat :as crosscat]))

(defn stat-types
  "Returns a map of column-name to GenSQL datatype.
   Args:
     `bdb-models`: a BayesDB export`"
  [bdb-models]
  (let [gensql-type (fn [bdb-type]
                      (case bdb-type
                        "nominal" :categorical
                        "numerical" :gaussian))
        bdb-types (get bdb-models :column-statistical-types)]
     (medley/map-vals gensql-type bdb-types)))

(defn view-latents
  "Returns the latents map required by gensql.inference for constructing a view dpmm.
  Args:
    `cluster-alpha` - The alpha parameter for clustering in this view.
    `clusters` - A vector of vectors containing row-ids. Each of the nested vectors represents a
      cluster."
  [cluster-alpha clusters]
  (let [counts (map count clusters)
        counts-map (zipmap (repeatedly gensym) counts)
        cluster-ids (keys counts-map)

        ;; Mapping of row-id to cluster-id
        y (->> (for [[cid row-ids] (map vector cluster-ids clusters)]
                 (zipmap row-ids (repeat cid)))
            (apply merge))]
    {:alpha cluster-alpha
     :counts counts-map
     :y y}))

(defn xcat
  "Returns a XCat record given a model from a BayesDB export.
  Args:
    `data` - A vector of maps representing the data the model was trained on.
    `stat-types` - A map of column name to GenSQL datatype
    `categories` - A map of categorical column name to category options.
    `model` - A map representing a single model from a BayesDB export."
  [data stat-types categories model]
  (let [{column-partition :column-partition
         clusters-per-view :clusters
         cluster-alphas :cluster-crp-hyperparameters
         column-hypers :column-hypers} model

         views (for [[columns clusters cluster-alpha] (map vector column-partition clusters-per-view cluster-alphas)]
                 {:spec {:hypers (select-keys column-hypers columns)}
                  :latents (view-latents cluster-alpha clusters)})

         view-names (repeatedly gensym)
         view-specs (zipmap view-names (map :spec views))
         xcat-spec {:views view-specs
                    :types stat-types}

         view-latents (zipmap view-names (map :latents views))
         ;; Global alpha not included in BayseDB export. Using a default value instead.
         xcat-latents {:global {:alpha 0.5}
                       :local view-latents}]
    (crosscat/construct-xcat-from-latents xcat-spec xcat-latents data {:options categories})))

(defn keywordize-bdb-export
  "Returns a bdb-export with all keys and column name references keywordized.
  Args:
    `bdb-export` - A map representing a BaysedDB export."
  [bdb-export]
  (let [keywordize (fn [column-partition]
                     (walk/postwalk #(if (string? %) (keyword %) %) column-partition))
        keywordize-column-partitions (fn [models] (for [model models]
                                                    (update model :column-partition keywordize)))]
    (-> bdb-export
        (walk/keywordize-keys)
        ;; We keywordize the nested vectors of column names present
        ;; at the paths [:models model-num :column-partition]
        (update :models keywordize-column-partitions))))

(defn xcat-gpms
  "Returns a sequence of XCat records given a BayesDB export.
  A BayesDB export might contain multiple models. Therefore, we return a sequence of XCat records.

  Args:
    `bdb-export` - A map representing the BayesDB export. The columns names referenced by the export
      need not reference keywordized column names.
    `rows` - A vector of maps representing the data the BayesDB export was trained on. Keys
      in `rows` should be keywordized. And values in `rows` should be cast according to the
      datasets' schema.
  Returns:
    A sequence of XCat records. These records will reference keywordized column names even if the
      original `bdb-export` did not."
  [bdb-export data]
  (let [bdb-export (keywordize-bdb-export bdb-export)
        data (into {} (map-indexed vector data)) ; Map of row-id to row;
        stat-types (stat-types bdb-export)
        categories  (get bdb-export :categories)]
    (for [model (get bdb-export :models)]
      (xcat data stat-types categories model))))
