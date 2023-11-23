#!/usr/bin/env python

import argparse
import itertools
import json
import numpy as np
import pandas as pd
from scipy.spatial import distance
import sppl.compilers.spe_to_dict as spe_to_dict
from sppl.transforms import Identity as I
import sys

def tvd(P, Q):
    return 0.5 * sum([np.abs(p-q) for p,q in zip(P,Q)])

def write(path, l):
    with open(path, "w") as f:
        l_str = ", ".join(l)
        f.write(f'({l_str})')

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
        "-o",
        "--output",
        type=argparse.FileType("w+"),
        default=sys.stdout,
        metavar="PATH",
    )
    parser.add_argument(
        "--worst-fit",
        type=str,
        metavar="PATH",
    )
    parser.add_argument(
        "--best-fit",
        type=str,
        metavar="PATH",
    )


    args = parser.parse_args()
    spe_dict = json.load(args.model)
    spe = spe_to_dict.spe_from_dict(spe_dict)

    df = pd.read_csv(args.data)

    result = {"c1":[], "c2":[], "tvd":[], "js":[],}
    cols = [c for c in df.columns if c!="age"]
    for c1, c2 in itertools.combinations(cols, 2):
        emp_p_df = df[[c1,c2]].value_counts(normalize=True)
        p_emp =  []
        p_model = []
        for i, (e1, e2) in enumerate(emp_p_df.index):
            p = emp_p_df.loc[(e1, e2)]
            if  p > 0:
                p_model.append(np.exp(spe.logpdf({I(c1):e1, I(c2):e2})))
                p_emp.append(p)
        if p_emp:
            result["c1"].append(c1)
            result["c2"].append(c2)
            result["tvd"].append(tvd(p_model, p_emp))
            result["js"].append(distance.jensenshannon(p_model, p_emp))

    output = pd.DataFrame(result)
    output.sort_values(by="tvd", inplace=True, ascending=False)
    output.to_csv(args.output, index=False)
    worst_fit = list(set(output.c1.tolist()[0:4] + output.c2.tolist()[0:4]))
    write(args.worst_fit, worst_fit)
    output.sort_values(by="tvd", inplace=True)
    best_fit = list(set(output.c1.tolist()[0:4] + output.c2.tolist()[0:4]))
    write(args.best_fit, best_fit)


if __name__ == "__main__":
    main()
