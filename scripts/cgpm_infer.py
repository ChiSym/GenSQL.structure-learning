#!/usr/bin/env python

import argparse
import cgpm.utils.general as general
import json
import itertools
import math
import pandas as pd
import sys
import yaml

from cgpm.crosscat.state import State


def replace(array, pred, replacement):
    """Destructively replace all instances in a 2D array that satisfy a
    predicate with a replacement.
    """
    return [[(y if not pred(y) else replacement) for y in x] for x in array]


def main():
    parser = argparse.ArgumentParser(description="")

    parser.add_argument(
        "metadata",
        type=argparse.FileType("r"),
        help="CGPM metadata JSON",
        default=sys.stdin,
        metavar="PATH",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w+"),
        default=sys.stdout,
        metavar="PATH",
    )
    parser.add_argument(
        "--data", type=argparse.FileType("r"), help="Path to numericalized CSV."
    )
    parser.add_argument(
        "-k",
        "--kernel",
        action="append",
        type=str,
        help="Inference kernel.",
        default=["alpha", "view_alphas", "column_hypers"],
        metavar="KERNEL",
        dest="kernels",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        help="Number of inference iterations",
        default=None,
        metavar="NUM",
    )
    parser.add_argument(
        "--minutes",
        type=float,
        help="Minutes inference should run.",
        default=None,
        metavar="NUM",
    )
    parser.add_argument(
        "--params", type=argparse.FileType("r"), help="Path to params.yaml"
    )
    parser.add_argument("--seed", type=int, default=1, help="CGPM seed.")

    args = parser.parse_args()

    if args.metadata is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    metadata = json.load(args.metadata)
    metadata["X"] = replace(metadata["X"], lambda x: x is None, math.nan)

    # XXX: Constraining depedence only works if the columns are incorporated exactly as in the same
    # order as in the data.
    df = pd.read_csv(args.data)
    column_mapping = {c: i for i, c in enumerate(df.columns)}
    cgpm_params = yaml.safe_load(args.params)["cgpm"]
    do_not_transition = []

    # We can't transition columns that are constrained to be dependent.
    if "dependence" in cgpm_params:
        Zv = dict(metadata["Zv"])
        for target_column, columns_to_move in cgpm_params["dependence"].items():
            for column_to_move in columns_to_move:
                Zv[column_mapping[column_to_move]] = Zv[column_mapping[target_column]]
                do_not_transition.append(column_mapping[column_to_move])
            do_not_transition.append(column_mapping[target_column])
        metadata["Zv"] = Zv
        # If we deleted a view all together, we need ensure that it's not around
        # in Zrv anymore.
        view_ids = list(Zv.values())
        Zrv = dict(metadata["Zrv"])
        for view_id in list(Zrv.keys()):
            if not view_id in view_ids:
                del Zrv[view_id]
        metadata["Zrv"] = Zrv
    columns_transition = [i for i in range(df.shape[1]) if i not in do_not_transition]
    rng = general.gen_rng(args.seed)
    # Indepdence is solved using CGPM's independence constraints.
    if "independence" in cgpm_params:
        Ci = []
        for c1, cols in cgpm_params["independence"].items():
            for c2 in cols:
                Ci.append(tuple([column_mapping[c1], column_mapping[c2]]))
    else:
        Ci = []
    metadata["Ci"] = Ci
    state = State.from_metadata(metadata, rng=rng)

    if do_not_transition:
        # Update hyper-parameters for columns you want to fix.
        state.transition(
            N=30, kernels=["column_hypers"], cols=do_not_transition, progress=False
        )
    if args.iterations is not None:
        state.transition(
            N=args.iterations, kernels=args.kernels, cols=columns_transition
        )
    if args.minutes is not None:
        state.transition(
            S=args.minutes * 60, kernels=args.kernels, cols=columns_transition
        )
    if do_not_transition:
        # Update hyper-parameters once more for columns kept fixed.
        state.transition(
            N=10, kernels=["column_hypers"], cols=do_not_transition, progress=False
        )

    state_metadata = state.to_metadata()
    state_metadata["X"] = replace(state_metadata["X"], math.isnan, None)
    json.dump(state_metadata, args.output)


if __name__ == "__main__":
    main()
