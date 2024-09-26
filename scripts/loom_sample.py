import loom.tasks
import pandas as pd
from StringIO import StringIO
import argparse
import json

def synthetic_sample_loom(num_samples):
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
    return df

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
    parser.add_argument(
        "-i",
        "--inv-mapping-table",
        type=str,
        help="Path to inverted mapping table in JSON",
        default=None,
    )

    args = parser.parse_args()

    with open(args.inv_mapping_table, "r") as f:
        inv_mapping_table = json.load(f)

    df =  synthetic_sample_loom(args.sample_count)
    for c, mapping in inv_mapping_table.items():
        new_c = [mapping.get(str(v),None) for v in df[c]]
        df[c] = new_c
    df.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
