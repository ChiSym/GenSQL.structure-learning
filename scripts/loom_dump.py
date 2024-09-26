#!/usr/bin/env python

import argparse
import distributions.io.stream as stream
import itertools
import json
import loom.cFormat as cFormat
import loom.schema_pb2 as schema_pb2
import os
import json
import sys
import pandas as pd

def loom_metadata(path, data):
    model_in = os.path.join(path, "model.pb.gz")
    assign_in = os.path.join(path, "assign.pbs.gz")
    cross_cat = schema_pb2.CrossCat()
    with stream.open_compressed(model_in, "rb") as f:
        cross_cat.ParseFromString(f.read())


    # Map col name to index.
    df = pd.read_csv(data)
    col_mapping = {c:i for i,c in enumerate(df.columns)}
    # Initialize hyper-parameter field.
    hypers = [None for _ in df.columns]

    with open("data/loom-feature-encoding.json", "r") as f:
        feature_encoding = json.load(f)
    zv = list(
        itertools.chain.from_iterable(
            [
                [(loom_rank, k) for loom_rank in kind.featureids]
                for k, kind in enumerate(cross_cat.kinds)
            ]
        )
    )
    num_kinds = len(cross_cat.kinds)
    assignments = {
        a.rowid: [a.groupids(k) for k in range(num_kinds)]
        for a in cFormat.assignment_stream_load(assign_in)
    }
    rowids = sorted(assignments)
    zrv = [
        [k, [assignments[rowid][k] for rowid in rowids]] for k in range(num_kinds)
    ]
    # From Loom docs: "'topology' hyperparameters for the Pitman-Yor categorization of features".
    structure_hypers = {
            "alpha": cross_cat.topology.alpha,
            "discount": cross_cat.topology.d
    }
    view_structure_hypers = []
    schema = {}
    # From Loom docs: "'clustering' hyperparameters for the Pitman-Yor
    # categorization of rows".
    for k, kind in enumerate(cross_cat.kinds):
        # Keep track of ordering in different places.
        dd_counter = 0
        nich_counter = 0
        view_structure_hypers.append({
            "alpha": kind.product_model.clustering.alpha,
            "discount": kind.product_model.clustering.d
        })
        for feature_id in kind.featureids:
            # XXX: currently only deals with categoricals (dd) and normals
            # (nich).
            col_name = feature_encoding[feature_id]["name"]
            col_type = feature_encoding[feature_id]["model"]
            if col_type == "dd":
                alphas = kind.product_model.dd[dd_counter].alphas
                assert len(alphas) == len(feature_encoding[feature_id]["symbols"]), \
                    "categories mapped incorrectly"
                hypers[col_mapping[col_name]] = {"alpha_{i}".format(i=i):alpha for i, alpha in enumerate(alphas)}
                dd_counter+=1
            if col_type == "nich":
                m = kind.product_model.nich[nich_counter].mu
                r = kind.product_model.nich[nich_counter].kappa
                s = kind.product_model.nich[nich_counter].sigmasq
                nu = kind.product_model.nich[nich_counter].nu
                hypers[col_mapping[col_name]] = {"m":m, "r":r, "s":s, "nu":nu}
                nich_counter+=1
    return {
            "Zv": zv,
            "Zrv": zrv,
            "structure_hypers": structure_hypers,
            "view_structure_hypers": view_structure_hypers,
            "hypers":hypers,
            "hooked_cgpms": {}}


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        error = "{string} is not a path to a directory.".format(string=string)
        raise ValueError(error)


def main():
    description = "Write a Loom model to disk as CGPM state metadata."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("sample", type=dir_path, help="Path to Loom sample directory.")
    parser.add_argument(
        "--data", type=argparse.FileType("r"), help="Path to numericalized CSV."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w+"),
        help="File to write metadata JSON to.",
        default=sys.stdout,
    )

    args = parser.parse_args()

    if args.sample is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    metadata = loom_metadata(args.sample, args.data)
    json.dump(metadata, args.output)


if __name__ == "__main__":
    main()
