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
import pprint
import sppl.compilers.spn_to_dict as spn_to_dict
import sppl.distributions as distributions
import sppl.math_util as math_util

from collections import Counter
from collections import OrderedDict
from sppl.spn import ProductSPN
from sppl.spn import SumSPN
from sppl.transforms import Identity

pp = pprint.PrettyPrinter(indent=4)


def read_metadata(f):
    metadata = json.load(f)

    # When serializing its metadata to JSON CGPM represents some dictionaries
    # as lists of pairs. When deserializing them we need to do the conversion
    # in the other direciton.

    for k in ["view_alphas", "Zv", "Zrv"]:
        if k in metadata:
            metadata[k] = dict(metadata[k])

    # Other dictionaries are serialized as lists of values. We can convert them
    # back to dictionaries by zipping them with their keys (in this case, the
    # outputs).

    for k in ["cctypes", "distargs", "hypers"]:
        metadata[k] = dict(zip(metadata["outputs"], metadata[k]))

    # Finally one dictionary is serialized as a JSON object. This converts its
    # integer keys to strings. We need to reverse that process.

    metadata["suffstats"] = [
        {int(k): v for k, v in d.items()} for d in metadata["suffstats"]
    ]

    return metadata


def view_assignments_to_view_partition(view_assignments):
    partition = OrderedDict([])

    for k, v in view_assignments.items():
        x = hash(v)

        if x not in partition:
            partition[x] = []

        partition[x].append(k)

    return partition


def convert_primitive(
    Xs, output, cctype, hypers, suffstats, distargs, categorical_mapping
):

    if cctype == "bernoulli":
        alpha = hypers["alpha"]
        beta = hypers["beta"]
        N = suffstats["N"]
        x_sum = suffstats["x_sum"]
        # Compute the distribution.
        p = (x_sum + alpha) / (N + alpha + beta)
        dist = distributions.bernoulli(p=p)

    elif cctype == "beta":
        strength = hypers["strength"]
        balance = hypers["balance"]
        # Compute the distribution.
        alpha = strength * balance
        beta = strength * (1.0 - balance)
        dist = distributions.beta(a=alpha, b=beta)

    elif cctype == "categorical":
        k = distargs["k"]
        alpha = hypers["alpha"]
        N = suffstats["N"]
        counts = suffstats["counts"]
        # Compute the distribution.
        weights = [alpha + counts[i] for i in range(k)]
        norm = sum(weights)
        if categorical_mapping is None:
            keys = map(str, range(k))
        else:
            keys = [categorical_mapping[output][j] for j in range(k)]
        dist = distributions.choice(
            {key: weight / norm for key, weight in zip(keys, weights)}
        )

    elif cctype == "crp":
        alpha = hypers["alpha"]
        N = suffstats["N"]
        counts = dict(suffstats["counts"])
        assert 1 <= len(counts)
        # Compute the distribution.
        tables = sorted(counts)
        weights = [counts[t] for t in tables] + [alpha]
        norm = sum(weights)
        keys = map(str, range(len(weights)))
        dist = {key: weight / norm for key, weight in zip(keys, weights)}

    elif cctype == "exponential":
        a = hypers["a"]
        b = hypers["b"]
        N = suffstats["N"]
        sum_x = suffstats["sum_x"]
        # Compute the distribution.
        an = a + N
        bn = b + sum_x
        dist = distributions.lomax(c=an, scale=bn)

    elif cctype == "geometric":
        a = hypers["a"]
        b = hypers["b"]
        N = suffstats["N"]
        sum_x = suffstats["sum_x"]
        # Compute the distribution.
        # The true posterior predictive resembles a beta negative binomial
        # distribution, which is not available in scipy.stats.
        # Thus we will return a geometric distribution centered at the
        # mean of the posterior distribution over the success probability.
        an = a + N
        bn = b + sum_x
        pn = an / (an + bn)
        dist = distributions.geom(p=pn)

    elif cctype == "normal":
        m = hypers["m"]
        r = hypers["r"]
        s = hypers["s"]
        nu = hypers["nu"]
        N = suffstats["N"]
        sum_x = suffstats["sum_x"]
        sum_x_sq = suffstats["sum_x_sq"]
        # Compute the distribution.
        # Refer to cgpm.tests.test_teh_murphy for the conversion of
        # hyperparameters into the Student T form.
        rn = r + N
        nun = nu + N
        mn = (r * m + sum_x) / rn
        sn = s + sum_x_sq + r * m * m - rn * mn * mn
        (an, bn, kn, mun) = (nun / 2, sn / 2, rn, mn)
        scalesq = bn * (kn + 1) / (an * kn)
        dist = distributions.t(df=2 * an, loc=mun, scale=math.sqrt(scalesq))

    elif cctype == "poisson":
        a = hypers["a"]
        b = hypers["b"]
        N = suffstats["N"]
        x_sum = suffstats["x_sum"]
        # Compute the distribution.
        # The implementation of Poisson.logpdf in CGPM is rather suspicious:
        # https://github.com/probcomp/cgpm/issues/251
        an = a + sum_x
        bn = b + N
        pn = bn / (1.0 + bn)
        dist = distributions.nbinom(n=an, p=pn)

    else:
        assert False, "Cannot convert primitive: %s " % (cctype,)

    return Xs[output] >> dist


def convert_cluster(Xs, Zs, metadata, categorical_mapping, tables):
    outputs = metadata["outputs"]

    def args(output, z):
        return (
            Xs,
            output,
            metadata["cctypes"][output],
            metadata["hypers"][output],
            metadata["suffstats"][output][z],
            metadata["distargs"][output],
            categorical_mapping,
        )

    children_x = [
        [convert_primitive(*args(output, z)) for output in outputs] for z in tables
    ]
    children_z = [
        [Zs[output] >> distributions.choice({str(z): 1}) for output in outputs]
        for z in tables
    ]
    children_list = [cx + cz for cx, cz in zip(children_x, children_z)]

    return [ProductSPN(children) for children in children_list]


def convert_view(Xs, Zs, metadata, categorical_mapping):
    # Compute the CRP cluster weights using Zr and alpha.
    Zr = metadata["Zr"]
    alpha = metadata["alpha"]
    counts = Counter(Zr)
    tables_existing = sorted(set(Zr))
    table_aux = max(tables_existing) + 1 if (len(tables_existing) > 0) else 0
    tables = tables_existing + [table_aux]
    weights = [counts[t] for t in tables_existing] + [alpha]
    log_weights = math_util.lognorm([math.log(w) for w in weights])

    # For each table, make the Product cluster.
    products = convert_cluster(Xs, Zs, metadata, categorical_mapping, tables)
    assert len(products) == len(log_weights)

    # Return a Sum of Products (or a single Product).
    return SumSPN(products, log_weights) if len(products) > 1 else products[0]


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
    # Check if we ran streaming inference and cannot guarantee that the indexes
    # in state.output agree with the column indeces in the traning data:
    if "incorporated_cols" in metadata:
        variable_mapping = dict(enumerate(metadata["incorporated_cols"]))
    else:
        variable_mapping = dict(enumerate(pandas.read_csv(args.data)))
    inv_variable_mapping = invert(variable_mapping)
    mapping_table = edn_format.loads(args.mapping_table.read())
    category_mapping = {
        inv_variable_mapping[k]: invert(v) for k, v in mapping_table.items()
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
