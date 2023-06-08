#!/usr/bin/env python

import argparse
import sys
import numpy as np
import pandas as pd

import json
import edn_format

from cgpm.utils.parallel_map import parallel_map
import sppl.compilers.spe_to_dict as spe_to_dict
from sppl.transforms import Identity as I

def ensure_clean(c):
    if c.startswith("("):
        return c[1:]
    elif c.endswith(")"):
        return c[:-1]
    else:
        return c

def not_null(v):
    if isinstance(v, str):
        return True
    elif v is None:
        return False
    else:
        return not np.isnan(v)

def save_samples(spe_samples, f):
    samples = [
        {
            edn_format.Keyword(k): v
            for k, v in row.items()
            if (not str(k).endswith("_cluster")) and (str(k) != "child")
        }
        for row in spe_samples
    ]
    f.write(edn_format.dumps(samples).replace("[", "(").replace("]", ")"))


def main():
    description = "Outputs samples from a SPPL model."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--model",
        type=argparse.FileType("r"),
        help="Path to SPE model (json) used to generate samples.",
    )
    parser.add_argument(
        "--test",
        type=argparse.FileType("r"),
        help="Path to CSV containing test data",
    )
    parser.add_argument(
        "--targets",
            nargs="+",
            default=[],
            help="Predict the following targets"
    )
    parser.add_argument(
            "--reweight",
            nargs="+",
            default=[],
            help="Reweight by the following columns"
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
    data = pd.read_csv(args.test)
    reweight_on = [ensure_clean(c) for c in args.reweight]
    targets = [ensure_clean(c) for c in args.targets]
    predictions = {target:[] for target in targets}
    def eval_row(i_row):
        _, row = i_row
        row = {I(c):row[c] for c in reweight_on if not_null(row[c])}
        spe_const = spe.constrain(row)
        output = {
            target: np.exp(spe_const.logpdf({I(target):"yes"}))
            for target in targets
        }
        return output
    predictions = parallel_map(eval_row, list(data.iterrows()))
    pd.DataFrame(predictions).to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
