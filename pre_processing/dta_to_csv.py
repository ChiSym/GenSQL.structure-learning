import argparse
import pandas as pd

def dta_to_csv(in_filename, out_filename):
    df = pd.read_stata(in_filename)

    df.to_csv(out_filename, index=False)

def main():
    description = ""
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--in_filename", type=str, help="Path to dta file.", default='../data/cumulative_2006-2022.dta'
    )

    parser.add_argument(
        "--out_filename", type=str, help="Target csv filename.", default="../data/full_data.csv"
    )

    args = parser.parse_args()

    dta_to_csv(args.in_filename, args.out_filename)

if __name__ == "__main__":
    main()