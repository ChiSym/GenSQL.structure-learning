(ns gensql.structure-learning.stream.transit
  "Defs for reading and writing gensql.inference gpms to transit-encoded strings."
  (:refer-clojure :exclude [reify])
  (:require [clojure.reflect :as cr]
            [cognitect.transit :as t]
            [gensql.inference.gpm.column :as column]
            [gensql.inference.gpm.compositional :as compositional]
            [gensql.inference.gpm.crosscat :as xcat]
            [gensql.inference.gpm.primitive-gpms.bernoulli :as bernoulli]
            [gensql.inference.gpm.primitive-gpms.categorical :as categorical]
            [gensql.inference.gpm.primitive-gpms.gaussian :as gaussian]
            [gensql.inference.gpm.view :as view])
  (:import (java.io ByteArrayOutputStream ByteArrayInputStream)
           (gensql.inference.gpm.column Column)
           (gensql.inference.gpm.compositional Compositional)
           (gensql.inference.gpm.crosscat XCat)
           (gensql.inference.gpm.primitive_gpms.bernoulli Bernoulli)
           (gensql.inference.gpm.primitive_gpms.categorical Categorical)
           (gensql.inference.gpm.primitive_gpms.gaussian Gaussian)
           (gensql.inference.gpm.view View)
           (java.nio.charset StandardCharsets)))

(def ^:private gensql-records
  "Record classes for GPMs from gensql.inference.
  NOTE: The actual Java classes need to be imported, not just the CLJ namespaces for the records."
  [Column Compositional XCat Bernoulli Categorical Gaussian View])

(defn ^:private record-write-handler
  "Produces a transit write handler given a record class `r`."
  [r]
  (let [classname (cr/typename r)]
    (t/write-handler (constantly classname) ; Tag is just the classname.
                     (fn [v] (into {} v))))) ; Value is the record as a map.

(def ^:private write-handlers-map
  "A map of transit write handlers for all the GPM record types in gensql.inference."
  (let [write-handlers (map record-write-handler gensql-records)]
    (zipmap gensql-records write-handlers)))

(def ^:private read-handlers-map
  "A map of transit read handlers for all the GPM record types in gensql.inference."
  (let [classnames (map cr/typename gensql-records)
        constructors [column/map->Column
                      compositional/map->Compositional
                      xcat/map->XCat
                      bernoulli/map->Bernoulli
                      categorical/map->Categorical
                      gaussian/map->Gaussian
                      view/map->View]
        read-handlers (map t/read-handler constructors)]
    (zipmap classnames read-handlers)))

(defn string
  "Takes an object and returns a transit-encoded string.
  Works with objects that have gpm records from gensql.inference."
  [obj]
  (let [transit-out (ByteArrayOutputStream. 4096)
        transit-writer (t/writer transit-out :json {:handlers write-handlers-map})]
    (t/write transit-writer obj)
    (.toString transit-out)))

(defn reify
  "Takes a transit-encoded string and returns a clj object."
  [transit-string]
  (let [in (ByteArrayInputStream. (.getBytes transit-string StandardCharsets/UTF_8))
        reader (t/reader in :json {:handlers read-handlers-map})]
    (t/read reader)))
