#!/usr/bin/env python

import itertools
import numpy as np
import pandas as pd
import scipy.stats as stats
import sys
import csv
import yaml
import argparse
import json
import edn_format
import sppl.compilers.spn_to_dict as spn_to_dict
from sppl.transforms import Identity as I

if not hasattr(stats, "frechet_r"):
    stats.frechet_r = stats.weibull_max

if not hasattr(stats, "frechet_l"):
    stats.frechet_l = stats.weibull_min


def get_predicate(c, v):
    if isinstance(v, list):
        return I(c) << set(v)
    elif isinstance(v, float):
        return I(c) > v


def main():
    description = "Outputs samples from a SPPL model."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--model",
        type=argparse.FileType("r"),
        help="Path to SPN model (json) used to generate samples.",
    )
    parser.add_argument(
        "--mapping-table",
        type=argparse.FileType("r"),
        help="Path to Loom mapping table.",
        dest="mapping_table",
    )
    parser.add_argument(
        "--data", type=argparse.FileType("r"), help="Path to ignored CSV."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w+"),
        help="Path to which samples will be written as EDN.",
        default=sys.stdout,
    )
    parser.add_argument("--seed", type=int, default=1, help="CGPM seed.")

    args = parser.parse_args()
    spn_dict = json.load(args.model)
    spn = spn_to_dict.spn_from_dict(spn_dict)
    np.random.seed(args.seed)
    mapping_table = edn_format.loads(args.mapping_table.read())
    df = pd.read_csv(args.data)
    with open("params.yaml", "r") as stream:
        params = yaml.safe_load(stream)

    configs = params["mi"]["configs"]
    if configs is None:
        # Set default value.
        configs = {}

    cols = [
        k.__str__()
        for k in spn.sample(1)[0].keys()
        if not k.__str__().endswith("_cluster")
    ]
    for c in cols:
        if c not in configs:
            if c in mapping_table:
                categories = list(mapping_table[c].keys())
                config = np.random.choice(
                    categories, size=int(np.floor(len(categories) / 2))
                ).tolist()
                configs[c] = config
            else:
                configs[c] = df[c].median()
    pairs = list(itertools.combinations(cols, 2))
    result = {"mi": {c: {} for c in cols}}
    for c1, c2 in pairs:
        p1 = get_predicate(c1, configs[c1])
        p2 = get_predicate(c2, configs[c2])
        mi = spn.mutual_information(p1, p2)
        result["mi"][c1][c2] = mi
        result["mi"][c2][c1] = mi
    result["configs"] = configs
    json.dump(result, args.output, indent=4)


if __name__ == "__main__":
    main()
