(ns inferenceql.structure-learning.code
  "Functions for converting multimixture ASTs to Gen.clj programs."
  (:require [babashka.fs :as fs]
            [clojure.edn :as edn]
            [clojure.string :as string]
            [zprint.core :as zprint]))

(defn with-ns
  "Amends a symbol with the provided namespace, if it is not nil."
  [sym ns]
  (if-not ns
    sym
    (symbol (name ns) (name sym))))

(defmulti ^:private distribution->form
  "Converts a distribution parameter map from a multimixture AST to a Gen.clj
  form."
  (fn [distribution & _]
    (:distribution/type distribution)))

(defmethod distribution->form :distribution.type/student-t
  [{:student-t/keys [degrees-of-freedom location scale]} & {:keys [distribution-alias]}]
  (let [sym (with-ns 'student-t distribution-alias)]
    `(~sym ~degrees-of-freedom ~location ~scale)))

(defmethod distribution->form :distribution.type/categorical
  [{:categorical/keys [category->weight]} & {:keys [distribution-alias]}]
  (let [sym (with-ns 'categorical distribution-alias)]
    `(~sym ~category->weight)))

(defn ^:private cluster->form
  "Converts a cluster map from a multimixture AST to a Gen.clj form."
  [{:cluster/keys [column->distribution]} & {:as opts}]
  ;; (update-vals column->distribution #(distribution->form % opts))
  (reduce-kv (fn [m column distribution]
               (assoc m column `(~'dynamic/trace! ~column ~@(distribution->form distribution opts))))
             {}
             column->distribution))

(defn ^:private view->form
  [{:view/keys [clusters]} index & {:keys [ns-name] :as opts}]
  (let [weights (mapv :cluster/weight clusters)
        sym (with-ns 'categorical ns-name)]
    `(~'case (~'dynamic/trace! ~(str "view-" index "-cluster") ~sym ~weights)
      ~@(sequence (comp (map #(cluster->form % opts))
                        (map-indexed vector)
                        cat)
                  clusters))))

(defn form
  "Converts a multimixture AST to a Gen.clj form."
  [{:multimixture/keys [views]} & {:keys [fn-name] :as opts :or {fn-name 'generate-row}}]
  (let [index->symbol #(symbol (str "view-" % "-map"))]
    `(~'def ~fn-name
      (~'gen []
       (~'let ~(into []
                     (comp (map-indexed (fn [index view]
                                          [(index->symbol index) (view->form view index opts)]))
                           cat)
                     views)
        (~'merge ~@(map index->symbol (range (count views)))))))))

(defn ^:private ns-form
  "Returns a namespace form for a Gen.clj program."
  [& {:keys [ns-name distribution-alias]
      :or {ns-name 'inferenceql.generative-program}}]
  (assert (some? ns-name))
  `(~'ns ~ns-name
    (:require [~'gen.distribution.commons-math ~@(if distribution-alias
                                                   [:as distribution-alias]
                                                   [:refer '[categorical student-t]])]
              [~'gen.dynamic :as ~'dynamic :refer [~'gen]])))

(defn string
  "Converts a multimixture AST to a pretty-printed Gen.clj program."
  [ast & {:keys [width] :or {width 100} :as opts}]
  (let [form (form ast)
        pprint #(zprint/zprint-str % width {:style :community})]
    (->> (map pprint [(ns-form opts) form])
         (string/join (apply str (repeat 2 \newline))))))

(defn pprint-string
  "Pretty-prints the Gen.clj program representation of the multimixture AST at
  the specified path to standard out."
  [& {:keys [path] :as opts}]
  (assert (fs/exists? path))
  (assert (not (fs/directory? path)))
  (let [ast (-> (slurp path)
                (edn/read-string))
        s (string ast opts)]
    (print s)))
