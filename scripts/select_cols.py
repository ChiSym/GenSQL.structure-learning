import argparse
import pandas as pd
import yaml


def select_cols(params, in_filename, out_filename):
    df = pd.read_csv(in_filename)

    cols_to_keep = yaml.safe_load(params)["cols_to_keep"]

    if cols_to_keep is not None:
        df = df[cols_to_keep]

    df.to_csv(out_filename, index=False)


def main():
    description = ""
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--params", type=argparse.FileType("r"), help="Path to params.yaml"
    )

    parser.add_argument(
        "--in_filename", type=str, help="Path to source file.", default="data/data.csv"
    )

    parser.add_argument(
        "--out_filename",
        type=str,
        help="Target csv filename.",
        default="data/selected_cols_data.csv",
    )

    args = parser.parse_args()
    select_cols(args.params, args.in_filename, args.out_filename)


if __name__ == "__main__":
    main()
