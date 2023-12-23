(ns inferenceql.structure-learning.code.webapp
  (:require [babashka.fs :as fs]
            [clojure.data.json :as json]
            [clojure.edn :as edn]
            [com.stuartsierra.component :as component]
            [hiccup.core :as hiccup]
            [hiccup.page :as page]
            [inferenceql.structure-learning.ast :as ast]
            [inferenceql.structure-learning.code :as code]
            [ring.component.jetty :as jetty]
            [ring.middleware.file :as file]
            [ring.middleware.file-info :as file-info]
            [ring.middleware.params :as params]
            [ring.middleware.stacktrace :as stacktrace]
            [ruuter.core :as ruuter]))

(defn json
  [x]
  (json/write-str x {:escape-slash false}))

(defn columns-select
  [ast]
  [:select {:name "columns"
            :multiple true
            :size 10}
   (for [column (ast/columns ast)]
     [:option column])])

(def html
  [:html
   [:head
    [:title "Gen.clj programs"]

    [:script {:src "https://unpkg.com/htmx.org@1.9.3"
              :integrity "sha384-lVb3Rd/Ca0AxaoZg5sACe8FJKF0tnUgR2Kd7ehUOG5GCcROv5uBIZsOqovBAcWua"
              :crossorigin "anonymous"}]

    [:link {:rel "stylesheet" :href "https://fonts.xz.style/serve/inter.css"}]
    [:link {:rel "stylesheet" :href "https://cdn.jsdelivr.net/npm/@exampledev/new.css@1.1.2/new.min.css"}]

    [:link {:rel "stylesheet" :href "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github.min.css"}]
    [:script {:src "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"}]
    [:script {:src "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/languages/clojure.min.js"}]]
   [:body
    [:header [:h1 "Programs as code"]]
    (let [files (sort-by fs/file-name (map fs/file (fs/list-dir "data/ast" "*.edn")))]
      [:form {:hx-post "/code"
              :hx-target "#code"
              :style {:margin-bottom "10px"}}
       [:select {:name "filename"
                 :type "string"
                 :style {:margin-right "10px"}
                 :hx-get "/columns"
                 :hx-target "#columns"
                 :hx-params "*"}
        (for [file files]
          [:option {:value (fs/file-name file)} (fs/file-name file)])]
       (let [ast (-> (first files)
                     (slurp)
                     (edn/read-string))]
         [:div {:id "columns"}
          (columns-select ast)])
       [:div {:id "columns"}]
       [:button {:type "submit"
                 :variant "primary"}
        "Show program"
        [:span {:id "indicator"
                :class "htmx-indicator"}
         "..."]]])
    [:div {:id "code"}]]])

(defn columns-handler
  [request]
  (let [file (fs/file (str "data/ast/" (get (:params request) "filename")))]
    (if-not (fs/exists? (fs/file file))
      {:status 404}
      (let [ast (-> file
                    (slurp)
                    (edn/read-string))]
        {:status 200
         :headers {"Content-Type" "text/html"}
         :body (hiccup/html (columns-select ast))}))))

(defn code-handler
  [request]
  (let [{:strs [filename columns]} (:params request)
        columns (if (coll? columns)
                  columns
                  [columns])
        file (fs/file (str "data/ast/" filename))]
    (if-not (fs/exists? (fs/file file))
      {:status 404}
      (let [program (-> file
                        (slurp)
                        (edn/read-string)
                        (ast/select-columns columns)
                        (code/string))]
        {:status 200
         :headers {"Content-Type" "text/html"}
         :body (hiccup/html
                [:div
                 [:pre [:code {:class "language-clojure"} program]]
                 [:script "hljs.highlightAll();"]])}))))

(def routes
  [{:path "/"
    :method :get
    :response {:status 200
               :headers {"Content-Type" "text/html"}
               :body (page/html5 html)}}
   {:path "/columns"
    :method :get
    :response columns-handler}
   {:path "/code"
    :method :post
    :response code-handler}])

(defn route
  [request]
  (ruuter/route routes request))

(def handler
  (-> #'route
      (file/wrap-file ".")
      (params/wrap-params)
      (file-info/wrap-file-info)
      (stacktrace/wrap-stacktrace-web)))

(defonce http-server
  (jetty/jetty-server {:app {:handler #'handler} :port 3000}))

(defn start
  [& {:as _args}]
  (alter-var-root #'http-server component/start))

(comment

  (alter-var-root #'http-server component/start)
  (alter-var-root #'http-server component/stop)

  ,)
