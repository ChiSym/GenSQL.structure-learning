#!/usr/bin/env python

import argparse
from inferenceql_auto_modeling.cgpm import CGPMModel
import edn_format
import json
import pandas
import sys
import yaml


def main():
    description = "Generate CGPM metadata."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Path to CGPM metadata.",
        default=sys.stdout,
    )
    parser.add_argument(
        "--data", type=argparse.FileType("r"), help="Path to numericalized CSV."
    )
    parser.add_argument(
        "--schema", type=argparse.FileType("r"), help="Path to CGPM schema."
    )
    parser.add_argument(
        "--mapping-table",
        type=argparse.FileType("r"),
        help="Path to Loom mapping table.",
        dest="mapping_table",
    )
    parser.add_argument("--metadata", type=str, help="Path to input CGPM metadata.")
    parser.add_argument(
        "--model",
        type=str,
        help="Prior, can be one of 'CrossCat', 'DPMM', 'Independent'; currently not compatible with Loom.",
        default="CrossCat",
    )
    parser.add_argument(
        "--params", type=argparse.FileType("r"), help="Path to params.yaml"
    )
    parser.add_argument("--seed", type=int, default=1, help="CGPM seed.")

    args = parser.parse_args()

    if any(x is None for x in [args.data, args.schema, args.mapping_table]):
        parser.print_help(sys.stderr)
        sys.exit(1)

    df = pandas.read_csv(args.data)
    schema = edn_format.loads(args.schema.read(), write_ply_tables=False)
    mapping_table = edn_format.loads(args.mapping_table.read(), write_ply_tables=False)
    additional_metadata = (
        {"hooked_cgpms": {}} if args.metadata is None else json.load(args.metadata)
    )
    model = args.model
    cgpm_params = yaml.safe_load(args.params)["cgpm"]

    cgpm = CGPMModel.from_data(
        df,
        schema,
        mapping_table,
        args.seed,
        model=model,
        cgpm_params=cgpm_params,
        additional_metadata=additional_metadata,
    )

    cgpm.to_metadata(args.output)


if __name__ == "__main__":
    main()
