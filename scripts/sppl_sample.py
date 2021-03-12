#!/usr/bin/env python

import scipy.stats as stats
import sys
import csv

# Monkey patching this to work around https://github.com/scipy/scipy/pull/7838

if not hasattr(stats, "frechet_r"):
    stats.frechet_r = stats.weibull_max

if not hasattr(stats, "frechet_l"):
    stats.frechet_l = stats.weibull_min

import argparse
import json
import edn_format
import sppl.compilers.spn_to_dict as spn_to_dict


def save_samples(spn_samples, f):
    samples = [
        {
            edn_format.Keyword(k): v
            for k, v in row.items()
            if (not str(k).endswith("_cluster")) and (str(k) != "child")
        }
        for row in spn_samples
    ]
    f.write(edn_format.dumps(samples).replace("[", "(").replace("]", ")"))


def main():
    description = "Outputs samples from a SPPL model."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--model",
        type=argparse.FileType("r"),
        help="Path to SPN model (json) used to generate samples.",
    )
    parser.add_argument(
        "--data",
        type=argparse.FileType("r"),
        help="Path to CSV used to generate the SPN model.",
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
    spn_dict = json.load(args.model)
    spn = spn_to_dict.spn_from_dict(spn_dict)

    data = csv.reader(args.data)
    row_count = len(list(data)) - 1

    sample_count = args.sample_count or row_count
    samples = spn.sample(sample_count)
    save_samples(samples, args.output)


if __name__ == "__main__":
    main()
