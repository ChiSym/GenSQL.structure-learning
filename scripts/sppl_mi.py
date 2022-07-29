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
import sppl.compilers.spe_to_dict as spe_to_dict
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
        help="Path to SPE model (json) used to generate samples.",
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
    spe_dict = json.load(args.model)
    spe = spe_to_dict.spe_from_dict(spe_dict)
    np.random.seed(args.seed)
    mapping_table = edn_format.loads(args.mapping_table.read(), write_ply_tables=False)
    df = pd.read_csv(args.data)
    with open("params.yaml", "r") as stream:
        params = yaml.safe_load(stream)

    configs = params["mi"]["configs"]
    if configs is None:
        # Set default value.
        configs = {}

    cols = [
        k.__str__()
        for k in spe.sample(1)[0].keys()
        if not k.__str__().endswith("_cluster")
    ]
    cols.sort()

    # Switch to a fixed random seed (12) before selecting category options for categorical columns
    # that do not have MI config provided.
    np.random.seed(12)
    for c in cols:
        if c not in configs:
            if c in mapping_table:
                categories = list(mapping_table[c].keys())
                categories.sort()
                config = np.random.choice(
                    categories, size=int(np.floor(len(categories) / 2)), replace=False
                ).tolist()
                config.sort()
                configs[c] = config
            else:
                configs[c] = df[c].median()
    pairs = list(itertools.combinations(cols, 2))
    result = {"mi": {c: {} for c in cols}}

    # Switch back to provided random seed when doing MI calculations.
    np.random.seed(args.seed)
    for c1, c2 in pairs:
        p1 = get_predicate(c1, configs[c1])
        p2 = get_predicate(c2, configs[c2])
        mi = spe.mutual_information(p1, p2)
        result["mi"][c1][c2] = mi
        result["mi"][c2][c1] = mi
    result["configs"] = configs
    json.dump(result, args.output, indent=4)


if __name__ == "__main__":
    main()
