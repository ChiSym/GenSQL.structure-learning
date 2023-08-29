#!/usr/bin/env python

import argparse
import cgpm.utils.general as general
import edn_format
import json
import pandas
import sys
import numpy as np

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
        "--schema", type=argparse.FileType("r"), help="Path to CGPM schema."
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
    schema = edn_format.loads(args.schema.read(), write_ply_tables=False)
    mapping_table = edn_format.loads(args.mapping_table.read(), write_ply_tables=False)

    def n_categories(column):
        return len(mapping_table[column])

    def distarg(column):
        return {"k": n_categories(column)} if schema[column] == "categorical" else None

    cctypes = [schema[column] for column in df.columns]
    distargs = [distarg(column) for column in df.columns]

    if args.metadata is not None:
        additional_metadata = json.load(args.metadata)
    else:
        additional_metadata = {}

    Zv = dict(additional_metadata["Zv"])
    Zrv = dict(additional_metadata["Zrv"])
    hypers = additional_metadata["hypers"]

    col_ids = list(Zv.keys())
    view_ids = list(Zv.values())

    new_col_ids = []
    for i in range(df.shape[1]):
        if i not in col_ids:
           new_col_ids.append(i)
           Zv[i] = np.random.choice(view_ids)
           if cctypes[i] == "normal":
                hypers.append({"m": 0., "r": 1., "s": 1., "nu": 1.})
           elif cctypes[i] == "categorical":
                hypers.append({"alpha": 1.})
           else:
               raise ValueError()

    new_metadata = {"Zv":Zv, "Zrv":Zrv, "hypers":hypers, "hooked_cgpms":{}}

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

    metadata = {**base_metadata, **new_metadata}
    rng = general.gen_rng(args.seed)

    if args.metadata is not None:
        state = State.from_metadata(metadata, rng=rng)
    else:
        state = State(**metadata, rng=rng)

    state.transition(N=30,kernels=["column_hypers"],cols=new_col_ids, progress=False)
    state.transition(N=1,kernels=["columns"],cols=new_col_ids, progress=False)

    json.dump(state.to_metadata(), args.output)


if __name__ == "__main__":
    main()
