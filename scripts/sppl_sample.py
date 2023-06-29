#!/usr/bin/env python

import scipy.stats as stats
import sys
import pandas as pd

# Monkey patching this to work around https://github.com/scipy/scipy/pull/7838

if not hasattr(stats, "frechet_r"):
    stats.frechet_r = stats.weibull_max

if not hasattr(stats, "frechet_l"):
    stats.frechet_l = stats.weibull_min

import argparse
import json
import sppl.compilers.spe_to_dict as spe_to_dict
from sppl.transforms import Identity


def generate(spe, columns, N):
    spe_samples = spe.sample_subset(N, columns)
    sample_df = pd.DataFrame(
        [{str(k): v for k, v in row.items()} for row in spe_samples]
    )
    return sample_df


def main():
    description = "Outputs samples from a SPPL model."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--model",
        type=argparse.FileType("r"),
        help="Path to SPE model (json) used to generate samples.",
    )
    parser.add_argument(
        "--data",
        type=argparse.FileType("r"),
        help="Path to CSV used to generate the SPE model.",
    )
    parser.add_argument(
        "--sample_count",
        type=int,
        nargs="?",
        default=None,
        help="Number of joint simulations for QC",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w+"),
        help="Path to which samples will be written as EDN.",
        default=sys.stdout,
    )

    args = parser.parse_args()
    spe_dict = json.load(args.model)
    spe = spe_to_dict.spe_from_dict(spe_dict)

    data = pd.read_csv(args.data)
    row_count = len(data)

    sample_count = args.sample_count or row_count
    columns = [Identity(c) for c in data.columns]
    samples = generate(spe, sample_count, columns)
    samples.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
