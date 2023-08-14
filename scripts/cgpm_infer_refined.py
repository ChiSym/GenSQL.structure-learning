#!/usr/bin/env python

import argparse
import cgpm.utils.general as general
import json
import itertools
import math
import pandas as pd
import sys
import yaml
import numpy as np

from cgpm.crosscat.state import State

none_to_nan = lambda x: float('nan') if x is None else x
mapped_none_to_nan = lambda xs: list(map(none_to_nan, xs))

def refine_crp_hyper_grids(state, n=30):
    final_hyper = state.crp.hypers['alpha']
    new_grid = np.linspace(0.80 * final_hyper, 1.2 * final_hyper, n)
    state.crp.hyper_grids['alpha'] = new_grid

def refine_view_hyper_grids(state, cols, n=30):
    for idx, view in state.views.items():
        final_hyper = view.crp.hypers['alpha']
        new_grid = np.linspace(0.80 * final_hyper, 1.2 * final_hyper, n)
        state.views[idx].crp.hyper_grids['alpha'] = new_grid

def refine_dim_hyper_grids(state, cols, n=30):
    for col in cols:
        final_hypers = state.dim_for(col).hypers
        for name, val in final_hypers.items():
            new_grid = np.linspace(0.80 * val, 1.2 * val, n) 
            state.dim_for(col).hyper_grids[name] = new_grid

def main():
    parser = argparse.ArgumentParser(description="")

    parser.add_argument(
        "metadata",
        type=argparse.FileType("r"),
        help="CGPM metadata JSON after running cgpm_infer.py",
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

    if args.metadata == None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    metadata = json.load(args.metadata)
    metadata['X'] = list(map(mapped_none_to_nan, metadata['X'])) 

    # XXX: Constraining depedence only works if the columns are incorporated exactly as in the same
    # order as in the data.
    df = pd.read_csv(args.data)
    column_mapping = {c: i for i, c in enumerate(df.columns)}
    cgpm_params = yaml.safe_load(args.params)["cgpm"]
    do_not_transition = []

    # XXX dependence and independence assumptions unsupported
    # We can't transition columns that are constrained to be dependent.
    if "dependence" in cgpm_params or "independence" in cgpm_params:
        print('it is unsafe to refine parameter grids with dependence or ' + \
              'independence assumptions')
        sys.exit(1)
    else:
        Ci = []
    columns_transition = [i for i in range(df.shape[1]) if i not in do_not_transition]
    rng = general.gen_rng(args.seed)
    metadata["Ci"] = Ci
    state = State.from_metadata(metadata, rng=rng)

    refine_crp_hyper_grids(state)
    refine_view_hyper_grids(state, columns_transition)
    refine_dim_hyper_grids(state, columns_transition)

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
    state_metadata['X'] = list(map(mapped_none_to_nan, state_metadata['X'])) 
    json.dump(state_metadata, args.output)


if __name__ == "__main__":
    main()
