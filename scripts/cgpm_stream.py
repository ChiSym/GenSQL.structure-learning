#!/usr/bin/env python

import argparse
import cgpm.utils.general as general
import edn_format
import itertools
import json
import math
import os
import pandas as pd
import sys
from inf_prog import inf_prog
from inf_prog import init_stream

from stream_cat import Streamcat
from cgpm_infer import replace


def main():
    parser = argparse.ArgumentParser(description="Streaming inference")

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="PATH",
    )
    parser.add_argument(
        "--data", type=argparse.FileType("r"), help="Path to numericalized CSV."
    )
    parser.add_argument(
        "--schema", type=argparse.FileType("r"), help="Path to CGPM schema."
    )
    parser.add_argument(
        "--mapping-table",
        type=argparse.FileType("r"),
        help="Path to Loom mapping table.",
        dest="mapping_table",
    )
    parser.add_argument("--seed", type=int, default=1, help="CGPM seed.")

    args = parser.parse_args()

    df = pd.read_csv(args.data)
    schema = edn_format.loads(args.schema.read())
    mapping_table = edn_format.loads(args.mapping_table.read())

    def n_categories(column):
        return len(mapping_table[column])

    def distarg(column):
        return {"k": n_categories(column)} if schema[column] == "categorical" else None

    cctypes = [schema[column] for column in df.columns]
    distargs = [distarg(column) for column in df.columns]

    columns, rows = init_stream(df)
    metadata = dict(
        X=df.values,
        col_names=df.columns.tolist(),
        incorporated_cols=columns,
        incorporated_rows=rows,
        cctypes_orig_order=cctypes,
        distargs_orig_order=distargs,
        seed=args.seed,
    )

    model = Streamcat.from_metadata(metadata)
    model = inf_prog(model, args.seed)
    model_metadata = model.to_metadata()
    # Ensure we save the correct x corresponding to the correct values in
    # output.
    model_metadata["X"] = replace(model_metadata["X"], math.isnan, None)
    json.dump(model_metadata, open(args.output, "w"))


if __name__ == "__main__":
    main()
