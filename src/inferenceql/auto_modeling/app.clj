(ns inferenceql.auto-modeling.app
  (:require [selmer.parser :refer [render]]
            [selmer.util :refer [without-escaping]]))

(defn create [{template-path :template spec-path :spec renderer :renderer title :title
               :or {renderer "canvas"}}]
  (let [template (-> template-path str slurp)
        spec (-> spec-path str slurp)]
    (without-escaping
      (print (render template {:spec spec
                               :renderer (str renderer)
                               :title title})))))
