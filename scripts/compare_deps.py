import argparse
import json
import itertools
import numpy as np


def main():
    description = "Compare probability of dependence with linear tests"
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--deps",
        type=argparse.FileType("r"),
        help="Path to probability of dependence (json)",
    )
    parser.add_argument(
        "--linear",
        type=argparse.FileType("r"),
        help="Path to linear test results (json)",
    )
    parser.add_argument(
        "--upper",
        default=0.9,
        type=float,
        help="threshold upper",
    )
    parser.add_argument(
        "--lower",
        default=0.4,
        type=float,
        help="threshold lower",
    )
    parser.add_argument(
        "-p",
        default=0.05,
        type=float,
        help="threshold lower",
    )

    args = parser.parse_args()
    dep_prob = json.load(args.deps)
    linear = json.load(args.linear)

    pairs = itertools.combinations(
        [k for k in dep_prob.keys() if k != "Maximal number of views"], 2
    )
    false_neg = []
    true_pos = []
    for c1, c2 in pairs:
        dep = dep_prob[c1][c2]
        lin = linear[c1][c2]["p-value"]
        if (dep < args.lower) and (lin < args.p):
            false_neg.append(
                f"    {c1}---{c2}: Pr[dep]={np.round(dep, decimals=2)}, p={np.round(lin, decimals=2)}"
            )
        elif (dep > args.upper) and (lin > args.p):
            true_pos.append(
                f"    {c1}---{c2}: Pr[dep]={np.round(dep, decimals=2)}, p={np.round(lin, decimals=2)}"
            )
    print("======================= False negatives =======================")
    print("")
    if false_neg:
        for fn in false_neg:
            print(fn)
    else:
        print("-- No false negatives --")
    print("")
    print("===============================================================")
    print("")
    print("======= Detected relationships missed by standard stats =======")
    print("")
    if true_pos:
        for tn in true_pos:
            print(fn)
    else:
        print("-- No relationships detected misssed by standard stats --")
    print("")
    print("===============================================================")


if __name__ == "__main__":
    main()
