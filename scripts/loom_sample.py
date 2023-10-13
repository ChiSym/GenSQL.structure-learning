import loom.tasks
import pandas as pd
from StringIO import StringIO
import argparse


def synthetic_sample_loom(num_samples, output_path):
    server = loom.tasks.query("loom")

    row = {name: "" for name in server.feature_names}
    csv_headers = map(str, row.iterkeys())
    csv_values = map(str, row.itervalues())

    # Prepare streams for the server.
    outfile = StringIO()
    writer = loom.preql.CsvWriter(outfile, returns=outfile.getvalue)
    reader = iter([csv_headers] + [csv_values])

    # Obtain the prediction.
    server._predict(reader, num_samples, writer, False)
    output_csv = writer.result()

    csvStringIO = StringIO(output_csv)

    df = pd.read_csv(csvStringIO)

    df.to_csv(output_path, index=False)


def main():
    description = "Write a Loom synthetic data to disk"
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--sample_count",
        type=int,
        nargs="?",
        default=None,
        help="Number of joint simulations for QC",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="File to write samples to.",
    )

    args = parser.parse_args()

    synthetic_sample_loom(args.sample_count, args.output)


if __name__ == "__main__":
    main()