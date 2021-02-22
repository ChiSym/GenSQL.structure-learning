#!/usr/bin/env python

import argparse
import distributions.io.stream as stream
import itertools
import json
import loom.cFormat as cFormat
import loom.schema_pb2 as schema_pb2
import os
import sys


def loom_metadata(path):
    model_in = os.path.join(path, 'model.pb.gz')
    assign_in = os.path.join(path, 'assign.pbs.gz')
    cross_cat = schema_pb2.CrossCat()

    with stream.open_compressed(model_in, 'rb') as f:
        cross_cat.ParseFromString(f.read())
        zv = list(
            itertools.chain.from_iterable([
                [(loom_rank, k) for loom_rank in kind.featureids]
                for k, kind in enumerate(cross_cat.kinds)
            ])
        )
        num_kinds = len(cross_cat.kinds)
        assignments = {
            a.rowid: [a.groupids(k) for k in range(num_kinds)]
            for a in cFormat.assignment_stream_load(assign_in)
        }
        rowids = sorted(assignments)
        zrv = [
            [k, [assignments[rowid][k] for rowid in rowids]]
            for k in range(num_kinds)
        ]

        return {
            'Zv': zv,
            'Zrv': zrv,
            'hooked_cgpms': {}
        }


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        error = '{string} is not a path to a directory.'.format(string=string)
        raise ValueError(error)


def main():
    description = 'Write a Loom model to disk as CGPM state metadata.'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        'sample',
        type=dir_path,
        help='Path to Loom sample directory.'
    )
    parser.add_argument(
        '-o', '--output',
        type=argparse.FileType('w+'),
        help='File to write metadata JSON to.',
        default=sys.stdout
    )

    args = parser.parse_args()

    if (args.sample is None):
        parser.print_help(sys.stderr)
        sys.exit(1)

    metadata = loom_metadata(args.sample)
    json.dump(metadata, args.output)


if __name__ == "__main__":
    main()
