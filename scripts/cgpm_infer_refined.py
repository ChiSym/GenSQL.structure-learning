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

lift_to_ndarray = lambda l: np.array(l) if isinstance(l, list) else l

def refine_crp_hyper_grid(state, grid=None):
    if grid is None:
        final_hyper = state.crp.hypers['alpha']
        grid = np.linspace(0.80 * final_hyper, 1.2 * final_hyper, 30)
    state.crp.hyper_grids['alpha'] = lift_to_ndarray(grid)

def refine_view_hyper_grid(state, view_idx, grid=None):
    if view_idx not in state.views.keys():
        print(f'Warning: refinement for view {view_idx} provided, while ' +
               'this view does not exist.\nSkipping refinement')
        return
    if grid is None:
        final_hyper = state.views[view_idx].crp.hypers['alpha']
        grid = np.linspace(0.80 * final_hyper, 1.2 * final_hyper, 30)
    state.views[view_idx].crp.hyper_grids['alpha'] = lift_to_ndarray(grid)

def refine_dim_hyper_grid(state, col_idx, hyper, grid=None):
    if grid is None:
        final_hyper = state.dim_for(col_idx).hypers[hyper]
        grid = np.linspace(0.80 * final_hyper, 1.2 * final_hyper, 30)
    state.dim_for(col_idx).hyper_grids[hyper] = lift_to_ndarray(grid)

def refine_dim_hyper_grids(state, col_idx, grids=None):
    for hyper in state.dim_for(col_idx).hypers.keys():
        grid = grids[hyper] if grids is not None else None
        refine_dim_hyper_grid(state, col_idx, hyper, grid)

def default_refinement_grids(state):
    refinement_grids = {'crp': None, 'dim': {}, 'view': {}}
    for col in state.outputs:
        col_hypers = state.dim_for(col).hypers.keys()
        refinement_grids['dim'][col] = {hyper: None for hyper in col_hypers}
    for view_idx in state.views.keys():
        refinement_grids['view'][view_idx] = None
    return refinement_grids

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
        "--refined-grids",
        type=argparse.FileType("r"),
        default=None,
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
    
    if args.refined_grids is None:
        print('No refined grid specified. Using default refinement strategy.')
        refinement_grids = default_refinement_grids(state)
    else:
        refinement_grids = json.load(args.refined_grids)

    refine_crp_hyper_grid(state, refinement_grids['crp'])
    for col, hyper_grids in refinement_grids['dim'].items():
        for hyper, grid in hyper_grids.items():
            refine_dim_hyper_grid(state, int(col), hyper, grid)
    for view_idx, view_grid in refinement_grids['view'].items():
        refine_view_hyper_grid(state, view_idx, view_grid)

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
