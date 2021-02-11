#!/usr/bin/env python

import argparse
import cgpm.utils.general as general
import edn_format
import json
import pandas
import sys

from cgpm.crosscat.state import State


def read_metadata(f):
    metadata = json.load(f)

    for z in ['Zv', 'Zrv']:
        if z in metadata:
            metadata[z] = {int(k): metadata[z][k] for k in metadata[z]}

    return metadata


def main():
    description = 'Infers hyperparameters for CGPM metadata.'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        'metadata',
        type=argparse.FileType('r'),
        help='Path to CGPM metadata.',
        default=sys.stdin
    )
    parser.add_argument(
        '-o', '--output',
        type=argparse.FileType('w+'),
        help='Path to CGPM metadata.',
        default=sys.stdout
    )
    parser.add_argument(
        '--data',
        type=argparse.FileType('r'),
        help='Path to numericalized CSV.'
    )
    parser.add_argument(
        '--schema',
        type=argparse.FileType('r'),
        help='Path to CGPM schema.'
    )
    parser.add_argument(
        '--mapping-table',
        type=argparse.FileType('r'),
        help='Path to Loom mapping table.',
        dest='mapping_table'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=1,
        help='CGPM seed.'
    )

    args = parser.parse_args()

    if any(x is None for x in [args.data, args.schema, args.mapping_table]):
        parser.print_help(sys.stderr)
        sys.exit(1)

    df = pandas.read_csv(args.data)
    schema = edn_format.loads(args.schema.read())
    mapping_table = edn_format.loads(args.mapping_table.read())
    metadata = read_metadata(args.metadata)

    def n_categories(column):
        return len(mapping_table[column])

    def distarg(column):
        return {'k': n_categories(column)} \
            if schema[column] == 'categorical' \
            else None

    cctypes = [schema[column] for column in df.columns]
    distargs = [distarg(column) for column in df.columns]

    state = State(
        df.values,
        cctypes=cctypes,
        distargs=distargs,
        outputs=range(df.shape[1]),
        rng=general.gen_rng(args.seed),
        **metadata
    )

    json.dump(state.to_metadata(), args.output)


if __name__ == "__main__":
    main()
