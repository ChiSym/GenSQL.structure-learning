import argparse
import json
import pandas as pd
import itertools
import numpy as np
import sys


def dep_prob(cgpm_dicts, ci, cj):
    return np.mean(
        [float(cgpm_dict["Zv"][ci] == cgpm_dict["Zv"][cj]) for cgpm_dict in cgpm_dicts]
    )


def main():
    description = "Saves dep prob do disk"
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        nargs="+",
        type=argparse.FileType("r"),
        help="CGPM model JSON files.",
        default=[],
        metavar="MODEL",
        dest="models",
    )
    parser.add_argument(
        "--data", type=argparse.FileType("r"), help="Path to numericalized CSV."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w+"),
        help="Path to SPPL JSON.",
        default=sys.stdout,
    )
    args = parser.parse_args()
    cgpm_dicts = [json.load(model) for model in args.models]
    df = pd.read_csv(args.data)
    pairs = itertools.combinations(df.columns, 2)
    variable_mapping = {c: i for i, c in enumerate(df.columns)}
    deps = {}
    # Turn Zv into dicts for speed and accessibility:
    for cgpm_dict in cgpm_dicts:
        cgpm_dict["Zv"] = dict(cgpm_dict["Zv"])

    for c1, c2 in pairs:
        p = dep_prob(cgpm_dicts, variable_mapping[c1], variable_mapping[c2])
        if c1 in deps:
            deps[c1][c2] = p
        else:
            deps[c1] = {c2: p}
        if c2 in deps:
            deps[c2][c1] = p
        else:
            deps[c2] = {c1: p}

    json.dump(deps, args.output)


if __name__ == "__main__":
    main()
