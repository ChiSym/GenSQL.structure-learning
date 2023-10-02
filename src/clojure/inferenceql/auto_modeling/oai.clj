(ns inferenceql.auto-modeling.oai
  (:require [clojure.edn :as edn]
            [clojure.walk :as walk]
            [inferenceql.query.db :as db]
            [inferenceql.query.main :as query]
            [inferenceql.gpm.sppl :as sppl]
            [inferenceql.gpm.sppl :as sppl]
            [inferenceql.query.io :as io]
            [inferenceql.query.permissive :as permissive]
            [wkok.openai-clojure.api :as api]))

;; make this be it's own tool; see how to pull in models.

(def sub-model-path "data/")

(def ensemble-id 0)
(def ast (edn/read-string (slurp (str sub-model-path "ast/sample." ensemble-id ".edn"))))
(def spe-path (str sub-model-path "sppl/unmerged/sample." ensemble-id ".json"))

(defn cluster
  [view-id cluster-id]
  (:cluster/column->distribution (nth (:view/clusters (nth (:multimixture/views ast) view-id)) cluster-id)))

(def sys-intro "Imagine you are markerter. You are tasked with reading a clustering model and naming the clusters so they describe consumer segments. The clustering model is based on a table with different columns that can could indicate consumer segments. Every row in this table is a consumer. You fit a clustering model. Every cluster is a segment. The resulting clustering is encoded as a .edn datastructure.
  ")

(defn cluster-message
  [view-id cluster-id]
  {:role "user" :content (str
                           "Here is one cluster in this model in .edn format:"
                           "```"
                           (str (cluster view-id cluster-id))
                           "```")})


(def db (db/with-model (db/empty) :m (sppl/slurp spe-path)))

; TODO: how to set the temperature param here?
(defn segment-label
  [view-id cluster-id]
  {(:content (:message (first (:choices (api/create-chat-completion {:model "gpt-4"
                                                                     :messages [{:role "system" :content sys-intro}
                                                                                (cluster-message view-id cluster-id)
                                                                                {:role "assistant" :content "Summarize this segment with 3-5 words"}
                                                                                {:role "assistant" :content "Return nothing else. Only the 3-5 word summary"}]})))))
   {:view view-id :cluster cluster-id}})


; pick the first 3 clusters in view 2.
(def segments (into {}
                    [(segment-label 2 0)
                     (segment-label 2 1)
                     (segment-label 2 2)
                     ]))


(defn query-segment
  [segment-name]
  (let [
        _ (println segment-name)
        query-str (str "SELECT Book_Buyer, Exercise_Health_Grouping, Invest_Active
                       FROM (GENERATE * UNDER m CONDITIONED BY view_" (:view (get segments segment-name))
                         "_cluster = \""
                         (:cluster (get segments segment-name))
                        \"") LIMIT 10")
        _ (println query-str)]
  (permissive/query query-str (atom db))))

;(keys segments)
;(query-segment (first (keys segments)))
;(query-segment (second (keys segments)))
;(query-segment (nth (keys segments) 2))
