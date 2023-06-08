#!/usr/bin/env python

import argparse
import json
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
    description = (
        "Saves maximum number of views to disk; needed to create an ensemble SPPL later"
    )
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        nargs="+",
        type=argparse.FileType("r"),
        help="CGPM model JSON files.",
        default=[],
        metavar="MODEL",
        dest="models",
    )
    args = parser.parse_args()
    cgpm_dicts = [json.load(model) for model in args.models]

    for cgpm_dict in cgpm_dicts:
        cgpm_dict["Zv"] = dict(cgpm_dict["Zv"])

    # Get the maximal number of views; needed later to create an ensemble-SPE in
    # sppl_merge.py.
    max_n_views = max([len(set(cgpm_dict["Zv"].values())) for cgpm_dict in cgpm_dicts])
    sys.stdout.write(str(max_n_views))


if __name__ == "__main__":
    main()
