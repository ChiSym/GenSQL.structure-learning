#!/usr/bin/env python

import argparse
import cgpm.utils.general as general
import json
import sys

from cgpm.crosscat.state import State


def main():
    parser = argparse.ArgumentParser(description='')

    parser.add_argument(
        'metadata',
        type=argparse.FileType('r'),
        help='CGPM metadata JSON',
        default=sys.stdin,
        metavar='PATH'
    )
    parser.add_argument(
        '-o', '--output',
        type=argparse.FileType('w+'),
        default=sys.stdout,
        metavar='PATH'
    )
    parser.add_argument(
        '-k', '--kernel',
        action='append',
        type=str,
        help='Inference kernel.',
        default=['alpha', 'view_alphas', 'column_hypers'],
        metavar='KERNEL',
        dest='kernels'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        help='Number of hyperperameter inference iterations',
        default=1,
        metavar='NUM'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=1,
        help='CGPM seed.'
    )

    args = parser.parse_args()

    if (args.metadata is None):
        parser.print_help(sys.stderr)
        sys.exit(1)

    metadata = json.load(args.metadata)
    rng = general.gen_rng(args.seed)
    state = State.from_metadata(metadata, rng=rng)
    iterations = args.iterations

    state.transition(N=iterations, kernels=args.kernels)

    json.dump(state.to_metadata(), args.output)


if __name__ == "__main__":
    main()
