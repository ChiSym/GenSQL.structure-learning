#!/usr/bin/env python

import argparse
import pandas as pd
import sys
import json

def main():
    description = "Create a smaller subset of dataframe"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--data", type=argparse.FileType("r"), help="Path to numericalized CSV."
    )
    parser.add_argument(
        "--loom-schema", type=argparse.FileType("r"), help="Path to numericalized CSV."
    )
    parser.add_argument(
        "--ci", type=int, help="column index"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w+"),
        help="Path to CGPM metadata.",
        default=sys.stdout,
    )
    parser.add_argument(
        "--output-schema",
        type=argparse.FileType("w+"),
        default=sys.stdout,
    )
    args = parser.parse_args()
    df = pd.read_csv(args.data)
    column_subset = df.columns[0:args.ci].tolist()
    df[column_subset].to_csv(args.output, index=False)

    loom_schema = json.load(args.loom_schema)

    for c in df.columns:
        if c not in column_subset:
            del loom_schema[c]
    json.dump(loom_schema, args.output_schema)

if __name__ == "__main__":
    main()
