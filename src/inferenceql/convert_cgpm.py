# Copyright 2020 MIT Probabilistic Computing Project.
# See LICENSE.txt
# This file was originally written by @fsaad as part of this repo:
# https://github.com/probcomp/sum-product-cgpm
"""This module converts CrossCat models obtained from
cgpm (possibly through bayeslite, as an intermediary) to SPNs that can
be queried using SPQL."""

from fractions import Fraction
from collections import Counter
from collections import OrderedDict
from math import log
from math import sqrt

import sppl.distributions

from sppl.math_util import lognorm
from sppl.spn import ProductSPN
from sppl.spn import SumSPN
from sppl.spn import ExposedSumSPN
from sppl.transforms import Identity

# =====================================================================
# Converting primitive distributions.

def convert_primitive(Xs, output, cctype, hypers, suffstats, distargs,
        categorical_mapping):

    if cctype == 'bernoulli':
        alpha = hypers['alpha']
        beta = hypers['beta']
        N = suffstats['N']
        x_sum = suffstats['x_sum']
        # Compute the distribution.
        p = (x_sum + alpha) / (N + alpha + beta)
        dist = sppl.distributions.bernoulli(p=p)

    elif cctype == 'beta':
        strength = hypers['strength']
        balance = hypers['balance']
        # Compute the distribution.
        alpha = strength * balance
        beta = strength * (1. - balance)
        dist = sppl.distributions.beta(a=alpha, b=beta)

    elif cctype == 'categorical':
        k = distargs['k']
        alpha = hypers['alpha']
        N = suffstats['N']
        counts = suffstats['counts']
        # Compute the distribution.
        weights = [alpha + counts[i] for i in range(k)]
        norm = sum(weights)
        keys = map(str, range(k)) \
            if (categorical_mapping is None) else \
            [categorical_mapping[output][j] for j in range(k)]
        dist = {key : weight / norm for key, weight in zip(keys, weights)}

    elif cctype == 'crp':
        alpha = hypers['alpha']
        N = suffstats['N']
        counts = dict(suffstats['counts'])
        assert 1 <= len(counts)
        # Compute the distribution.
        tables = sorted(counts)
        weights = [counts[t] for t in tables] + [alpha]
        norm = sum(weights)
        keys = map(str, range(len(weights)))
        dist = {key : weight / norm for key, weight in zip(keys, weights)}

    elif cctype == 'exponential':
        a = hypers['a']
        b = hypers['b']
        N = suffstats['N']
        sum_x = suffstats['sum_x']
        # Compute the distribution.
        an = a + N
        bn = b + sum_x
        dist = sppl.distributions.lomax(c=an, scale=bn)

    elif cctype == 'geometric':
        a = hypers['a']
        b = hypers['b']
        N = suffstats['N']
        sum_x = suffstats['sum_x']
        # Compute the distribution.
        # The true posterior predictive resembles a beta negative binomial
        # distribution, which is not available in scipy.stats.
        # Thus we will return a geometric distribution centered at the
        # mean of the posterior distribution over the success probability.
        an = a + N
        bn = b + sum_x
        pn = an / (an + bn)
        dist = sppl.distributions.geom(p=pn)

    elif cctype == 'normal':
        m = hypers['m']
        r = hypers['r']
        s = hypers['s']
        nu = hypers['nu']
        N = suffstats['N']
        sum_x = suffstats['sum_x']
        sum_x_sq = suffstats['sum_x_sq']
        # Compute the distribution.
        # Refer to cgpm.tests.test_teh_murphy for the conversion of
        # hyperparameters into the Student T form.
        rn = r + N
        nun = nu + N
        mn = (r*m + sum_x)/rn
        sn = s + sum_x_sq + r*m*m - rn*mn*mn
        (an, bn, kn, mun) = (nun/2, sn/2, rn, mn)
        scalesq = bn*(kn+1)/(an*kn)
        dist = sppl.distributions.t(df=2*an, loc=mun, scale=sqrt(scalesq))

    elif cctype == 'poisson':
        a = hypers['a']
        b = hypers['b']
        N = suffstats['N']
        x_sum = suffstats['x_sum']
        # Compute the distribution.
        # The implementation of Poisson.logpdf in CGPM is rather suspicious:
        # https://github.com/probcomp/cgpm/issues/251
        an = a + sum_x
        bn = b + N
        pn = bn / (1. + bn)
        dist = sppl.distributions.nbinom(n=an, p=pn)

    else:
        assert False, 'Cannot convert primitive: %s ' % (cctype,)

    return Xs[output] >> dist

def convert_cluster(Xs, Zs, metadata, categorical_mapping, tables):
    outputs = metadata['outputs']
    cctypes = metadata['cctypes']
    hypers = metadata['hypers']
    distargs = metadata['distargs']
    suffstats = metadata['suffstats']
    args = lambda output, z : (Xs, output, cctypes[output], hypers[output],
        suffstats[output][z], distargs[output], categorical_mapping)
    children_list_x = [
        [convert_primitive(*args(output, z)) for output in outputs]
        for z in tables
    ]
    children_list_z = [
        [Zs[output] >> {str(z): 1} for output in outputs]
        for z in tables
    ]
    children_list = [cx + cz for cx, cz in zip(children_list_x, children_list_z)]
    return [ProductSPN(children) for children in children_list]

def convert_view(Xs, Zs, metadata, categorical_mapping):
    # Compute the CRP cluster weights using Zr and alpha.
    Zr = metadata['Zr']
    alpha = metadata['alpha']
    counts = Counter(Zr)
    tables_existing = sorted(set(Zr))
    table_aux = max(tables_existing) + 1 if (len(tables_existing) > 0) else 0
    tables = tables_existing + [table_aux]
    weights = [counts[t] for t in tables_existing] + [alpha]
    log_weights = lognorm([log(w) for w in weights])

    # For each table, make the Product cluster.
    products = convert_cluster(Xs, Zs, metadata, categorical_mapping, tables)
    assert len(products) == len(log_weights)

    # Return a Sum of Products (or a single Product).
    return SumSPN(products, log_weights) if len(products) > 1 else products[0]

def convert_state(metadata, variable_mapping, categorical_mapping):
    # Obtain the outputs.
    outputs = metadata['outputs']

    # Construct the symbolic variables.
    if variable_mapping is None:
        Xs = {o : Identity('X[%d]' % (o,)) for o in outputs}
        Zs = {o : Identity('Z[%d]' % (o,)) for o in outputs}
    else:
        variable_mapping = dict(variable_mapping)
        Xs = {o : Identity(variable_mapping[o]) for o in outputs}
        Zs = {o : Identity('%s_cluster' % (variable_mapping[o],)) for o in outputs}

    if categorical_mapping is not None:
        categorical_mapping = {o : dict(m) for o, m in categorical_mapping}

    # Extract column data.
    cctypes = {o: cc for o, cc in zip(outputs, metadata['cctypes'])}
    hypers = {o: h for o, h in zip(outputs, metadata['hypers'])}
    distargs = {o: d for o, d in zip(outputs, metadata['distargs'])}
    suffstats = {o: dict(s) for o, s in zip(outputs, metadata['suffstats'])}

    # Extract view data.
    Zv = dict(metadata['Zv'])
    view_alphas = dict(metadata['view_alphas'])
    Zrv = dict(metadata['Zrv'])

    # Construct the views.
    views = []
    view_partition = assignments_to_partition(Zv)
    for v, (view_idx, view_outputs) in enumerate(view_partition.items()):
        metadata_view = {
            'idx'       : v,
            'outputs'   : view_outputs,
            'cctypes'   : cctypes,
            'hypers'    : hypers,
            'distargs'  : distargs,
            'suffstats' : suffstats,
            'Zr'        : Zrv[view_idx],
            'alpha'     : view_alphas[view_idx],
        }
        view = convert_view(Xs, Zs, metadata_view, categorical_mapping)
        views.append(view)

    # Update the symbolic variable lookup dictionary to have string keys.
    if variable_mapping is not None:
        Xs = {variable_mapping[o] : s for o, s in Xs.items()}
        Zs = {variable_mapping[o] : s for o, s in Zs.items()}

    # Construct a Product of Sums (or a single Sum).
    spn = ProductSPN(views) if len(views) > 1 else views[0]

    # Return the SPN and variables.
    return Xs, Zs, spn

def convert_states(metadata_list, variable_mapping=None, categorical_mapping=None):
    # Arguments
    #
    # metadata_list : A list of return values from state.to_metadata().
    #
    # variable_mapping (optional) : A dictionary mapping integer variable
    #   numbers to string variable names,
    #   e.g., {0 : 'Age', 1 : 'Height', ...}
    #   Keys of this dictionary are the numbers in metadata['outputs'].
    #
    # categorical_mapping (optional) : a dictionary mapping integer variable
    #   numbers to a lookup dictionary for categorical variables,
    #   e.g. {0: {1: 'USA', 2: 'India'}, 1: {}}
    #   Keys of the outer dictionary are the numbers in metadata['outputs'].
    #   Keys of the inner dictionary are the outcomes of categorical variables.

    # Convert each state individually.
    results = [
        convert_state(
            metadata,
            variable_mapping=variable_mapping,
            categorical_mapping=categorical_mapping)
        for metadata in metadata_list
    ]
    Xs_list, Zs_list, children = [x for x in zip(*results)]
    assert all(Xs_list[0]==Xs for Xs in Xs_list)
    assert all(Zs_list[0]==Zs for Zs in Zs_list)

    # Create an equal-weighted ExposedSum.
    id_children = Identity('child')
    n_children = len(metadata_list)
    children_keys = [str(i) for i in range(n_children)]
    children_probs = {i: Fraction(1, n_children) for i in children_keys}
    children_dist = id_children >> children_probs
    children_dict = dict(zip(children_keys, children))
    spn_sum = ExposedSumSPN(children_dict, children_dist)

    # Add the symbolic variable for querying.
    spn = spn_sum if n_children > 1 else spn_sum.children[0]
    spn.child = id_children

    # Return the resulting SPN.
    return Xs_list[0], Zs_list[0], spn

def assignments_to_partition(d):
    partition = OrderedDict([])
    for k, v in d.items():
        x = hash(v)
        if x not in partition:
            partition[x] = []
        partition[x].append(k)
    return partition
