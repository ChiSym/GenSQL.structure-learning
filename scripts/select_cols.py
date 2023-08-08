import argparse
import pandas as pd


def select_cols(cols_to_keep, in_filename, out_filename):
    df = pd.read_csv(in_filename)

    df[cols_to_keep].to_csv(out_filename, index=False)

default_cols_to_keep = [
    "year",
    "state",
    "gender",
    "age",
    "educ",
    "race_h",
    "religion",
    "relig_imp",
    "marstat",
    "ownhome",
    "has_child",
    "no_milstat",
    "vv_turnout_gvm",
    "pid7",
    "ideo5",
    "faminc",
    "employ",
    "no_healthins",
    "union",
    "economy_retro",
    "newsint",
    "approval_pres",
    "voted_pres_party",
]

def main():
    description = ""
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--cols_to_keep",
        type=int,
        help="columns to keep",
        default=default_cols_to_keep,
    )

    parser.add_argument(
        "--in_filename", type=str, help="Path to source file.", default="data/full_data.csv"
    )

    parser.add_argument(
        "--out_filename", type=str, help="Target csv filename.", default="data/selected_cols_data.csv"
    )

    args = parser.parse_args()
    select_cols(args.cols_to_keep, args.in_filename, args.out_filename)

if __name__ == "__main__":
    main()