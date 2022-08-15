#!/usr/bin/env bb

(require '[clojure.java.shell :as shell])

;; Define what to prompt to the users if the relevant git configs are not set.
(def messages {"user.name" "Git user name is not set. Please input your username here:",
               "user.email" "Git email address is not set. Please input an email address here:"})

(defn input-config [config-target]
  "Read a specific git configuration from the commandline."
  (println (messages config-target))
  (println ">")
  (let [input-val (read-line)]
    (shell/sh "sh"
              "-c"
              (str "git config --global " config-target " " input-val))))

(defn get-config-target [config-target]
  "Ensure that git is fully configured for auto-modeling."
  (let [{exit :exit out :out err :err} (shell/sh "sh"
                                                 "-c"
                                                 (str "git config " config-target))]
    (if (empty? err)
      (when-not (zero? exit)
        (input-config config-target))
      (throw (Exception. err)))))

;; Initializes quitely.
(shell/sh "sh" "-c" "git init -q")

(get-config-target "user.name")

(get-config-target "user.email")

(println "git is configured. You can start to use auto-modeling!")

(shutdown-agents)
