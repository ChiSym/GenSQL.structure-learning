#!/usr/bin/env python

import argparse
import cgpm.utils.general as general
import json
import math
import sys

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
    parser.add_argument("--seed", type=int, default=1, help="CGPM seed.")

    args = parser.parse_args()

    if args.metadata is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    metadata = json.load(args.metadata)
    metadata["X"] = replace(metadata["X"], lambda x: x is None, math.nan)
    rng = general.gen_rng(args.seed)
    state = State.from_metadata(metadata, rng=rng)
    if args.iterations is not None:
        state.transition(N=args.iterations, kernels=args.kernels)
    if args.minutes is not None:
        state.transition(S=args.minutes * 60, kernels=args.kernels)

    state_metadata = state.to_metadata()
    state_metadata["X"] = replace(state_metadata["X"], math.isnan, None)
    json.dump(state_metadata, args.output)


if __name__ == "__main__":
    main()
