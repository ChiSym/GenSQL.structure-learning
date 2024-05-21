#!/usr/bin/env python

import argparse
import pandas as pd
import yaml


def load_csv(csv_file):
    """Load a csv file within data/fidelity/."""
    df = pd.read_csv(f"data/fidelity/{csv_file}")
    # Next, some hacking to help keep plot labels short.
    df["model"] = csv_file.replace(".csv", "").replace("synthetic-data-", "")
    df["index"] = range(len(df))
    return df


def main():
    parser = argparse.ArgumentParser(description="Process a list of strings.")
    parser.add_argument(
        "--params",
        type=argparse.FileType("r"),
        help="Path to params.yaml",
    )
    args = parser.parse_args()

    csv_files = yaml.safe_load(args.params)["synthetic_data_evaluation"]["datasets"]

    df = pd.concat([load_csv(csv_file) for csv_file in csv_files])
    print(df.to_json(orient="records"))


if __name__ == "__main__":
    main()
