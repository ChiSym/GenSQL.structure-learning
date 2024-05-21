#!/usr/bin/env python

import argparse
import json
import polars as pl
from lpm_discretize import discretize_quantiles


def main():
    parser = argparse.ArgumentParser(description="Process a list of strings.")
    parser.add_argument(
        "--real",
        metavar="r",
        type=str,
        help="Input: path to a CSV file with real data in data/.",
    )
    parser.add_argument(
        "--synthetic",
        metavar="S",
        type=str,
        help="Input: path to a CSV file with synthetic data in data/.",
    )
    parser.add_argument(
        "--schema", type=argparse.FileType("r"), help="Input: path to CGPM schema."
    )
    parser.add_argument(
        "--real-disc",
        type=str,
        help="Output: path to a CSV file with discretized real data in data/discretized/.",
    )
    parser.add_argument(
        "--synthetic-disc",
        type=str,
        help="Output: path to a CSV file with discretized synthetic data in data/discretized/.",
    )
    parser.add_argument(
        "--quantiles",
        type=int,
        default=4,
        help="Number of quantiles used for discretization, optional.",
    )
    args = parser.parse_args()

    # Read both csv files.
    df_real = pl.read_csv(args.real)
    df_synthetic = pl.read_csv(args.synthetic)

    # Read schema. Use Loom schema so that we can remain lightweight, i.e.
    # using JSON and not edn_format
    schema = json.load(args.schema)

    # Get discretized version of the dataframes above. Use Polar's types do decide what to discretize.
    # By default, this discretizes with based on quartiles in `df_real`, as it's
    # the firt entry in the list...
    df_real_discretized, df_synthetic_discretized = discretize_quantiles(
        [df_real, df_synthetic],
        quantiles=args.quantiles,
        columns=[c for c in df_real.columns if schema[c] in ["nich", "gp"]],
    )
    df_real_discretized.write_csv(args.real_disc)
    df_synthetic_discretized.write_csv(args.synthetic_disc)


if __name__ == "__main__":
    main()
