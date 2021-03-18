(ns inferenceql.auto-modeling.package
  "Utility functions used by the package.sh script."
  (:require [clojure.edn :as edn]
            [clojure.pprint :refer [pprint]]))

(defn local-git-deps
  "Removes the iql.inference and iql.query git deps from deps.edn.
  Replaces them with filesystem deps."
  [_]
  (let [deps (-> (slurp *in*)
                 (edn/read-string)
                 (assoc-in [:deps 'probcomp/inferenceql.inference]
                           {:local/root "inferenceql.inference/"})
                 (assoc-in [:deps 'probcomp/inferenceql.query]
                           {:local/root "inferenceql.query/"}))]
    (binding [*print-namespace-maps* false
              clojure.pprint/*print-right-margin* 80
              clojure.pprint/*print-miser-width* 80]
      (pprint deps))))

(defn get-sha
  "Gets the sha of a particular dependency in a deps.edn."
  [{:keys [dep-name]}]
  (let [deps (-> (slurp *in*)
                 (edn/read-string))]
    (print (get-in deps [:deps dep-name :sha]))))
