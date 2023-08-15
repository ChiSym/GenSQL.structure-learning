#!/usr/bin/env python

import argparse
import edn_format
import itertools
import json
import pandas
import sys
import numpy as np
import scipy.stats as stats
import warnings
from collections import defaultdict

# Monkey patching this to work around https://github.com/scipy/scipy/pull/7838
infinite_F = 1e10  # large value to use for writing infinity to json

if not hasattr(stats, "frechet_r"):
    stats.frechet_r = stats.weibull_max

if not hasattr(stats, "frechet_l"):
    stats.frechet_l = stats.weibull_min


def placeholder_stats(stattypes):
    match stattypes:
        case ["numerical", "numerical"]:
            return {
                "slope": 0.0,
                "intercept": 0.0,
                "r-value": 0.0,
                "p-value": 1.0,
            }
        case ["nominal", "nominal"]:
            return {"chi2": 0, "p-value": 1, "dof": 0}
        case ["nominal", "numerical"] | ["numerical", "nominal"]:
            return {"F": 0, "p-value": 1}
        case _:
            raise ValueError(stattypes)


def compute_stats(stattypes, xs, ys):
    match stattypes:
        case ["numerical", "numerical"]:
            return lin_reg(xs, ys)
        case ["nominal", "nominal"]:
            return chi_squared(xs, ys)
        case ["nominal", "numerical"]:
            return anova(xs, ys)
        case ["numerical", "nominal"]:
            return anova(ys, xs)
        case _:
            raise ValueError(stattypes)


def lin_reg(xs, ys):
    """Compute linear regression if we have data on both xs and ys"""
    r = stats.linregress(xs, ys)
    return {
        "slope": r.slope,
        "intercept": r.intercept,
        "r-value": r.rvalue,
        "p-value": r.pvalue,
    }


def chi_squared(xs, ys):
    """Compute chi-square statistic"""
    contingency = pandas.crosstab(xs, ys)
    chi2, p, dof, expected = stats.chi2_contingency(contingency)
    return {"chi2": chi2, "p-value": p, "dof": dof}


def anova(c1, c2):
    """Compute One-way ANOVA"""
    samples = defaultdict(list)
    for categorical_value, continuous_value in zip(c1, c2):
        samples[categorical_value].append(continuous_value)

    if len(samples) > 1:
        warnings.filterwarnings("error")
        # ANOVA warnings from https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.f_oneway.html
        try:
            F, p = stats.f_oneway(*samples.values())
        except stats.ConstantInputWarning:
            # Raised if all values within each of the input arrays are identical.
            # In this case the F statistic is either infinite or isn’t defined, so np.inf or
            # np.nan is returned.
            return {"F": infinite_F, "p-value": 0}
        except stats.DegenerateDataWarning:
            # Raised if the length of any input array is 0, or if all the input arrays have length 1.
            # np.nan is returned for the F statistic and the p-value in these cases.
            return {"F": 0, "p-value": 1}

    return {"F": 0, "p-value": 1}


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

    pairs = itertools.permutations(df.columns, 2)

    results = defaultdict(dict)

    for c1, c2 in pairs:
        stattypes = [schema[c1].name, schema[c2].name]
        if "ignore" in stattypes:
            continue
        pair_df = df[[c1, c2]].dropna()

        if len(pair_df) <= 1:
            results[c1][c2] = placeholder_stats(stattypes)

        else:
            c1_vals = pair_df[c1].values
            c2_vals = pair_df[c2].values

            results[c1][c2] = compute_stats(stattypes, c1_vals, c2_vals)

    json.dump(results, args.output)


if __name__ == "__main__":
    main()
