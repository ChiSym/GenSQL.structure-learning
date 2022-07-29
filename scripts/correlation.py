#!/usr/bin/env python

import argparse
import edn_format
import itertools
import json
import pandas
import sys
import numpy as np
import scipy.stats as stats
from edn_format import Keyword
from collections import defaultdict

# Monkey patching this to work around https://github.com/scipy/scipy/pull/7838

if not hasattr(stats, "frechet_r"):
    stats.frechet_r = stats.weibull_max

if not hasattr(stats, "frechet_l"):
    stats.frechet_l = stats.weibull_min


def lin_reg(xs, ys):
    """Compute linear regression if we have data on both xs and ys"""
    if len(xs) > 0:  # Check whether nan mask return data
        r = stats.linregress(xs, ys)
        # Check if stats.linregress ran into numerical problems.
        if not (np.isnan(r.slope) or np.isnan(r.intercept)):
            return {
                "slope": r.slope,
                "intercept": r.intercept,
                "r-value": r.rvalue,
                "p-value": r.pvalue,
            }
    # Else: return a placeholder that works with subsequent dvc stages.
    return {
        "slope": 0.0,
        "intercept": 0.0,
        "r-value": 0.0,
        "p-value": 1.0,
    }


def main():
    description = "Outputs linear correlation info for all pairs of numerical columns."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--data",
        type=argparse.FileType("r"),
        help="Path to CSV used to generate correlations.",
    )
    parser.add_argument(
        "--schema", type=argparse.FileType("r"), help="Path to base schema."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w+"),
        help="Path to which correlation information will be written as a csv.",
        default=sys.stdout,
    )

    args = parser.parse_args()
    df = pandas.read_csv(args.data)

    schema = edn_format.loads(args.schema.read(), write_ply_tables=False)

    numerical_cols = [
        column
        for column, stattype in schema.items()
        if stattype == Keyword("numerical")
    ]
    pairs = itertools.combinations(numerical_cols, 2)

    regressions = defaultdict(dict)

    for c1, c2 in pairs:
        c1_vals = df[c1].values
        c2_vals = df[c2].values

        nan_mask = ~np.isnan(c1_vals) & ~np.isnan(c2_vals)

        # Store c1, c2 regression.
        r_items_1 = lin_reg(c1_vals[nan_mask], c2_vals[nan_mask])
        regressions[c1][c2] = r_items_1
        r_items_2 = lin_reg(c2_vals[nan_mask], c1_vals[nan_mask])
        regressions[c2][c1] = r_items_2

    json.dump(regressions, args.output)


if __name__ == "__main__":
    main()
