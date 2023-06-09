#!/usr/bin/env python
# coding: utf-8


import argparse
import json
import sppl.compilers.spe_to_dict as spe_to_dict
import matplotlib.pyplot as plt
import pandas as pd
import sys
import numpy as np

from sppl.transforms import Identity

def generate(model, columns, limit):
    samples = model.sample_subset([Identity(c) for c in columns], limit)
    d = {c:[] for c in columns}
    for s in samples:
        for c in columns:
            d[c].append(s[Identity(c)])
    return pd.DataFrame(d)[columns]

def main():
    description = "Outputs samples from a SPPL model."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--model",
        type=argparse.FileType("r"),
        help="Path to SPE model (json) used to generate samples.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Path to synthetic-csv",
        default=sys.stdout,
    )
    parser.add_argument(
        "--data",
        type=argparse.FileType("r"),
        help="Path to CSV used to generate the SPE model.",
    )

    args = parser.parse_args()
    spe_dict = json.load(args.model)
    spe = spe_to_dict.spe_from_dict(spe_dict)


    df = pd.read_csv(args.data)

    df_synth = generate(spe, df.columns, len(df))

    df_synth.to_csv(args.output, index=False)

if __name__ == "__main__":
    main()
