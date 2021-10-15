#!/usr/bin/env python

import scipy.stats as stats
import sys

# Monkey patching this to work around https://github.com/scipy/scipy/pull/7838

if not hasattr(stats, "frechet_r"):
    stats.frechet_r = stats.weibull_max

if not hasattr(stats, "frechet_l"):
    stats.frechet_l = stats.weibull_min

import argparse
import edn_format
import json
import sppl.compilers.spn_to_dict as spn_to_dict

from sppl.spn import ProductSPN
from sppl.transforms import Identity
from sppl_import import read_metadata, view_assignments_to_view_partition, convert_view


def main():
    description = ""
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--metadata",
        type=argparse.FileType("r"),
        help="Path to CGPM metadata.",
        default=sys.stdin,
    )
    parser.add_argument(
        "--data", type=argparse.FileType("r"), help="Path to numericalized CSV."
    )
    parser.add_argument(
        "--mapping-table",
        type=argparse.FileType("r"),
        help="Path to Loom mapping table.",
        dest="mapping_table",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w+"),
        help="Path to SPPL JSON.",
        default=sys.stdout,
    )

    args = parser.parse_args()

    if any(x is None for x in [args.metadata, args.data, args.mapping_table]):
        parser.print_help(sys.stderr)
        sys.exit(1)

    def invert(d):
        return {v: k for k, v in d.items()}

    metadata = read_metadata(args.metadata)
    variable_mapping = dict(enumerate(metadata["col_names"]))
    inv_variable_mapping = invert(variable_mapping)
    mapping_table = edn_format.loads(args.mapping_table.read())
    category_mapping = {
        inv_variable_mapping[k]: invert(v)
        for k, v in mapping_table.items()
        if k in metadata["col_names"]
    }

    outputs = metadata["outputs"]
    Xs = {o: Identity(variable_mapping[o]) for o in outputs}
    Zs = {o: Identity(f"{variable_mapping[o]}_cluster") for o in outputs}

    views = []
    view_partition = view_assignments_to_view_partition(metadata["Zv"])
    for v, (view_idx, view_outputs) in enumerate(view_partition.items()):
        metadata_view = {
            "idx": v,
            "outputs": view_outputs,
            "cctypes": metadata["cctypes"],
            "hypers": metadata["hypers"],
            "distargs": metadata["distargs"],
            "suffstats": metadata["suffstats"],
            "Zr": metadata["Zrv"][view_idx],
            "alpha": metadata["view_alphas"][view_idx],
        }
        view = convert_view(Xs, Zs, metadata_view, category_mapping)
        views.append(view)

    # Construct a Product of Sums (or a single Sum).
    spn = ProductSPN(views) if len(views) > 1 else views[0]

    json.dump(spn_to_dict.spn_to_dict(spn), args.output)


if __name__ == "__main__":
    main()
