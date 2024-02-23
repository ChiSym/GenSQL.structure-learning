#!/usr/bin/env python

import argparse
import cgpm.utils.general as general
import duckdb
import edn_format
import json
import pandas
import sys

from cgpm.crosscat.state import State


def main():
    description = "Generate CGPM metadata."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w+"),
        help="Path to CGPM metadata.",
        default=sys.stdout,
    )
    parser.add_argument(
        "--data", type=argparse.FileType("r"), help="Path to numericalized CSV."
    )
    parser.add_argument(
        "--schema", help="Path to schema."
    )
    parser.add_argument(
        "--mapping-table",
        type=argparse.FileType("r"),
        help="Path to Loom mapping table.",
        dest="mapping_table",
    )
    parser.add_argument(
        "--metadata", type=argparse.FileType("r"), help="Path to input CGPM metadata."
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Prior, can be one of 'CrossCat', 'DPMM', 'Independent'; currently not compatible with Loom.",
        default="CrossCat",
    )
    parser.add_argument("--seed", type=int, default=1, help="CGPM seed.")

    args = parser.parse_args()

    if any(x is None for x in [args.data, args.schema, args.mapping_table]):
        parser.print_help(sys.stderr)
        sys.exit(1)

    df = pandas.read_csv(args.data)
    schema = duckdb.read_csv(args.schema, header=True)
    stattypes = dict(duckdb.sql("SELECT column_name, column_cgpm_statistical_type FROM schema").fetchall())
    mapping_table = edn_format.loads(args.mapping_table.read(), write_ply_tables=False)

    def n_categories(column):
        return len(mapping_table[column])

    def distarg(column):
        return {"k": n_categories(column)} if stattypes[column] == "categorical" else None

    cctypes = [stattypes[column] for column in df.columns]
    distargs = [distarg(column) for column in df.columns]

    if args.metadata is not None:
        additional_metadata = json.load(args.metadata)
    else:
        additional_metadata = {}

    base_metadata = dict(
        X=df.values, cctypes=cctypes, distargs=distargs, outputs=range(df.shape[1])
    )
    if args.model == "CrossCat":
        pass  # don't constrain the model space further.
    elif args.model == "DPMM":
        base_metadata["Zv"] = {i: 0 for i in range(len(cctypes))}
    elif args.model == "Independent":
        base_metadata["Zv"] = {i: i for i in range(len(cctypes))}
        cluster_idx = [0] * df.shape[0]
        base_metadata["Zrv"] = {i: cluster_idx for i in range(df.shape[1])}
    else:
        raise ValueError(f"Model '{args.model}' not definied")

    metadata = {**base_metadata, **additional_metadata}
    rng = general.gen_rng(args.seed)

    if args.metadata is not None:
        state = State.from_metadata(metadata, rng=rng)
    else:
        state = State(**metadata, rng=rng)

    json.dump(state.to_metadata(), args.output)


if __name__ == "__main__":
    main()
