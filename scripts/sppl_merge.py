#!/usr/bin/env python

import scipy.stats as stats
import sys

# Monkey patching this to work around https://github.com/scipy/scipy/pull/7838

if not hasattr(stats, "frechet_r"):
    stats.frechet_r = stats.weibull_max

if not hasattr(stats, "frechet_l"):
    stats.frechet_l = stats.weibull_min

import argparse
import json
import sppl.compilers.spe_to_dict as spe_to_dict
import sppl.distributions as distributions

from fractions import Fraction
from sppl.spe import ExposedSumSPE
from sppl.transforms import Identity


def main():
    description = "Merges multiple SPPL models."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        nargs="+",
        type=argparse.FileType("r"),
        help="SPPL model JSON.",
        default=[],
        metavar="MODEL",
        dest="models",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w+"),
        help="Path to write joined SPPL model JSON.",
        default=sys.stdout,
    )

    args = parser.parse_args()

    if not len(args.models) > 0:
        parser.print_help(sys.stderr)
        sys.exit(1)

    spe_dicts = [json.load(model) for model in args.models]
    children = [spe_to_dict.spe_from_dict(d) for d in spe_dicts]

    # Create an equal-weighted ExposedSum.
    id_children = Identity("child")
    n_children = len(children)
    children_keys = [str(i) for i in range(n_children)]
    children_probs = {i: Fraction(1, n_children) for i in children_keys}
    children_dist = id_children >> distributions.choice(children_probs)
    children_dict = dict(zip(children_keys, children))
    spe_sum = ExposedSumSPE(children_dict, children_dist)

    # Add the symbolic variable for querying.
    spe = spe_sum if n_children > 1 else spe_sum.children[0]
    spe.child = id_children

    json.dump(spe_to_dict.spe_to_dict(spe), args.output)


if __name__ == "__main__":
    main()
