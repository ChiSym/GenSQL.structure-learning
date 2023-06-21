#!/usr/bin/env python

import argparse
import edn_format
import pandas as pd


def main():
    description = "Show meta data on data sued "
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--data", type=str, default="data/data.csv", help="Path to data CSV."
    )
    parser.add_argument(
        "--show", action="store_true", help="Print 10 randomly sampled rows"
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Read data schema and add contents to metadata.",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.data)

    # Meta data table names
    name_field = "Column name"
    dtype_field = "Data type"
    unique_field = "# unique values"
    missing_field = "# missing values"

    meta = {
        name_field: df.columns.tolist(),
        dtype_field: df.dtypes.tolist(),
        unique_field: [],
        missing_field: [],
    }
    for c in df.columns:
        meta[unique_field].append(df[c].unique().shape[0])
        meta[missing_field].append(sum(df[c].isnull()))
    # If users wants to, add schema.
    if args.schema:
        with open("data/schema.edn", "r") as f:
            schema = edn_format.loads(f.read(), write_ply_tables=False)
        meta["Statistical type"] = [schema[c].name for c in df.columns]

    meta_df = pd.DataFrame(meta)
    meta_df.set_index(name_field, inplace=True)

    print("-------------------------------")
    print(f"# rows: {df.shape[0]}")
    print(f"# cols: {df.shape[1]}")
    print("-------------------------------")
    if args.show:
        print("")
        print("Print 10 randomly sampled rows")
        print(df.sample(10))
        print("")
        print("-------------------------------")
    print(meta_df.to_string())
    print("-------------------------------")


if __name__ == "__main__":
    main()
