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
import math
import pandas
import sppl.compilers.spe_to_dict as spe_to_dict
import sppl.distributions as distributions
import sppl.math_util as math_util

from collections import Counter
from collections import OrderedDict
from edn_format import Keyword
from sppl.spe import ProductSPE
from sppl.spe import SumSPE
from sppl.transforms import Identity


def convert_primitive(column_name, primitive):
    primitive_distribution_type = primitive[Keyword("distribution/type")]

    if primitive_distribution_type == Keyword("distribution.type/categorical"):
        dist = distributions.choice(primitive[Keyword("categorical/category->weight")])

    elif primitive_distribution_type == Keyword("distribution.type/student-t"):
        dist = distributions.t(
            df=primitive[Keyword("student-t/degrees-of-freedom")],
            loc=primitive[Keyword("student-t/location")],
            scale=primitive[Keyword("student-t/scale")],
        )

    elif primitive_distribution_type == Keyword("distribution.type/negative-binom"):
        dist = distributions.nbinom(
            n=primitive[Keyword("negative-binom/n")],
            p=primitive[Keyword("negative-binom/p")],
        )

    else:
        assert False, "Cannot convert primitive type: %s " % (
            primitive_distribution_type,
        )

    # Return a leaf node:
    return Identity(column_name) >> dist


def convert_cluster(view_index, cluster_index, cluster):
    # Compute the component product
    cluster_product_children = [convert_primitive(k, v) for k, v in cluster.items()]
    # Create a variable capturing the cluster index.
    cluster_product_children.append(
        Identity(f"view_{view_index}_cluster")
        >> distributions.choice({str(cluster_index): 1})
    )
    return ProductSPE(cluster_product_children)


def convert_view(view_index, view):
    # Get all cluster weights.
    log_weights = math_util.lognorm(
        [math.log(cluster[Keyword("cluster/weight")]) for cluster in view]
    )
    # For each table, make the Product cluster.
    products = [
        convert_cluster(
            view_index,
            cluster_index,
            cluster[Keyword("cluster/column->distribution")],
        )
        for cluster_index, cluster in enumerate(view)
    ]

    # Return a Sum of Products (or a single Product).
    return SumSPE(products, log_weights) if len(products) > 1 else products[0]


def main():
    description = ""
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--multi-mix-ast",
        type=argparse.FileType("r"),
        help="Path to multi-mix-ast.",
        default=sys.stdin,
    )
    parser.add_argument(
        "--output",
        type=argparse.FileType("w+"),
        help="Path to SPPL JSON.",
        default=sys.stdout,
    )

    args = parser.parse_args()
    if args.multi_mix_ast is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    multi_mix_ast = edn_format.loads(args.multi_mix_ast.read(), write_ply_tables=False)

    # For each view, return the clustering (i.e. the sums of products).
    views = [
        convert_view(view_index, view_ast[Keyword("view/clusters")])
        for view_index, view_ast in enumerate(
            multi_mix_ast[Keyword("multimixture/views")]
        )
    ]

    # Construct a Product of Sums (or a single Sum).
    spe = ProductSPE(views) if len(views) > 1 else views[0]
    json.dump(spe_to_dict.spe_to_dict(spe), args.output)


if __name__ == "__main__":
    main()
