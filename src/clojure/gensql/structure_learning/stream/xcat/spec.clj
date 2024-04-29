(ns gensql.structure-learning.stream.xcat.spec
  "Utility functions for producing xcat specs from xcat records."
  (:require [medley.core :as medley]))

(defn xcat->spec [xcat]
  {:views (->> (:views xcat)
               (medley/map-vals (fn [view]
                                  {:hypers (medley/map-vals :hyperparameters (:columns view))})))
   :types (->> (:views xcat)
               vals
               (mapcat :columns)
               (into {})
               (medley/map-vals :stattype))})

(defn xcat->latents [xcat]
  (let [global-alpha (-> xcat :latents :alpha)
        local  (medley/map-vals :latents (:views xcat))]
    {:global {:alpha global-alpha}
     :local local}))

(defn xcat->full-spec [xcat]
  {:num-rows (-> xcat :views first val :columns first val :data count)
   :spec (xcat->spec xcat)
   :latents (xcat->latents xcat)})
