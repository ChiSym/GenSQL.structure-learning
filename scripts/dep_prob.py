import argparse
import json
import pandas as pd
import itertools
import numpy as np
import sys


def dep_prob(cgpm_dicts, c1, c2, variable_mappings):
    return np.mean(
        [
            float(
                cgpm_dict["Zv"][variable_mappings[i][c1]]
                == cgpm_dict["Zv"][variable_mappings[i][c2]]
            )
            for i, cgpm_dict in enumerate(cgpm_dicts)
        ]
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

    # We assume that all passed in models have the same columns incorporated.
    if "col_names" in cgpm_dicts[0]:
        pairs = itertools.combinations(cgpm_dicts[0]["col_names"], 2)
        variable_mappings = [
            {c: i for i, c in enumerate(cgpm_dicts[0]["col_names"])}
        ] * len(cgpm_dicts)
    else:
        pairs = itertools.combinations(df.columns, 2)
        variable_mappings = [{c: i for i, c in enumerate(df.columns)}] * len(cgpm_dicts)

    deps = {}
    # Turn Zv into dicts for speed and accessibility:
    for cgpm_dict in cgpm_dicts:
        cgpm_dict["Zv"] = dict(cgpm_dict["Zv"])

    for c1, c2 in pairs:
        p = dep_prob(cgpm_dicts, c1, c2, variable_mappings)
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
