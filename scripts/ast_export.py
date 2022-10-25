#!/usr/bin/env python

import sys

import argparse
import edn_format
import json
import math
import pandas as pd
import sppl.math_util as math_util

from collections import Counter
from collections import OrderedDict


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


def export_primitive(output, cctype, hypers, suffstats, distargs, categorical_mapping):

    if cctype == "bernoulli":
        alpha = hypers["alpha"]
        beta = hypers["beta"]
        N = suffstats["N"]
        x_sum = suffstats["x_sum"]
        # Compute the distribution.
        p = (x_sum + alpha) / (N + alpha + beta)
        dist = {
            edn_format.Keyword("distribution/type"): edn_format.Keyword(
                "distribution.type/bernoulli"
            ),
            edn_format.Keyword("bernoulli/p"): p,
        }

    elif cctype == "beta":
        strength = hypers["strength"]
        balance = hypers["balance"]
        # Compute the distribution.
        alpha = strength * balance
        beta = strength * (1.0 - balance)
        dist = {
            edn_format.Keyword("distribution/type"): edn_format.Keyword(
                "distribution.type/beta"
            ),
            edn_format.Keyword("beta/alpha"): alpha,
            edn_format.Keyword("beta/beta"): beta,
        }

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
        dist = {
            edn_format.Keyword("distribution/type"): edn_format.Keyword(
                "distribution.type/categorical"
            ),
            edn_format.Keyword("categorical/category->weight"): {
                key: weight / norm for key, weight in zip(keys, weights)
            },
        }

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
        dist = {
            edn_format.Keyword("distribution/type"): edn_format.Keyword(
                "distribution.type/categorical"
            ),
            edn_format.Keyword("categorical/category->weight"): {
                key: weight / norm for key, weight in zip(keys, weights)
            },
        }

    elif cctype == "exponential":
        a = hypers["a"]
        b = hypers["b"]
        N = suffstats["N"]
        sum_x = suffstats["sum_x"]
        # Compute the distribution.
        an = a + N
        bn = b + sum_x
        # See: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.lomax.html
        dist = {
            edn_format.Keyword("distribution/type"): edn_format.Keyword(
                "distribution.type/lomax"
            ),
            edn_format.Keyword("lomax/c"): an,
            edn_format.Keyword("lomax/scale"): bn,
        }

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
        dist = {
            edn_format.Keyword("distribution/type"): edn_format.Keyword(
                "distribution.type/geometric"
            ),
            edn_format.Keyword("geometric/p"): pn,
        }

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
        dist = {
            edn_format.Keyword("distribution/type"): edn_format.Keyword(
                "distribution.type/student-t"
            ),
            edn_format.Keyword("student-t/degrees-of-freedom"): 2 * an,
            edn_format.Keyword("student-t/location"): mun,
            edn_format.Keyword("student-t/scale"): math.sqrt(scalesq),
        }

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
        # so, this get's transformed into a negative binominal: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.nbinom.html
        dist = {
            edn_format.Keyword("distribution/type"): edn_format.Keyword(
                "distribution.type/negative-binom"
            ),
            # Conventionally, the paramters of a binominal are called n and
            # p. Because math sucks.
            edn_format.Keyword("negative-binom/n"): an,
            edn_format.Keyword("negative-binom/p"): pn,
        }

    else:
        assert False, "Cannot convert primitive: %s " % (cctype,)

    return dist


def export_cluster(
    metadata, categorical_mapping, tables, log_weights, variable_mapping
):
    outputs = metadata["outputs"]

    def args(output, z):
        return (
            output,
            metadata["cctypes"][output],
            metadata["hypers"][output],
            metadata["suffstats"][output][z],
            metadata["distargs"][output],
            categorical_mapping,
        )

    children_x = [
        {
            edn_format.Keyword("cluster/weight"): math.exp(lw),
            edn_format.Keyword("cluster/column->distribution"): {
                variable_mapping[output]: export_primitive(*args(output, z))
                for output in outputs
            },
        }
        for lw, z in zip(log_weights, tables)
    ]
    return children_x


def export_view(metadata, categorical_mapping, variable_mapping):
    # Compute the CRP cluster weights using Zr and alpha.
    Zr = metadata["Zr"]
    alpha = metadata["alpha"]
    counts = Counter(Zr)
    tables_existing = sorted(set(Zr))
    table_aux = max(tables_existing) + 1 if (len(tables_existing) > 0) else 0
    tables = tables_existing + [table_aux]
    weights = [counts[t] for t in tables_existing] + [alpha]
    log_weights = math_util.lognorm([math.log(w) for w in weights])

    products = export_cluster(
        metadata, categorical_mapping, tables, log_weights, variable_mapping
    )

    return products


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
        help="Path to categorical mapping table.",
        dest="mapping_table",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w+"),
        help="Path to AST edn.",
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
        variable_mapping = dict(enumerate(pd.read_csv(args.data)))
    inv_variable_mapping = invert(variable_mapping)
    mapping_table = edn_format.loads(args.mapping_table.read(), write_ply_tables=False)
    category_mapping = {
        inv_variable_mapping[k]: invert(v) for k, v in mapping_table.items()
    }

    outputs = metadata["outputs"]

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
        view = export_view(metadata_view, category_mapping, variable_mapping)
        views.append({edn_format.Keyword("view/clusters"): view})

    args.output.write(
        edn_format.dumps({edn_format.Keyword("multimixture/views"): views}, indent=4)
    )


if __name__ == "__main__":
    main()
