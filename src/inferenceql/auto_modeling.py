# -*- coding: utf-8 -*-

# Copyright (c) 2020 MIT Probabilistic Computing Project

# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from cgpm.crosscat.state import State
from cgpm.utils import general as gu
from cgpm.utils.parallel_map import parallel_map
from copy import deepcopy
from inferenceql.convert_cgpm import convert_states

def replace_strings(df_in, schema):
    """Replace categorical values in a dataframe with integers as specified in
    the schema."""
    df = df_in.copy()
    for c in df.columns:
        if schema[c]['type'].lower() == 'nominal':
            df[c] = df_in[c].replace(to_replace=schema[c]['values'])
    return df


def replace(dict_in, values):
    return [dict_in[v.lower()] for v in values]


def create_cgpms(df, schema,  n_models=1, parallel=True):
    """
    Take data and schema and return a CGPM state.

    The CGPM API requires a numpy array with floats and integers only. Every column has
    to be modeled -- meaning ignored columns (as specified in the schema) need
    to be removed from this array while we keep track which index in the numpy
    array correspond to which column in the original dataframe.

    We  further need CGPM compatible data types and the distribution args (for
    us this corresponds only to arity for categoricals for now).

    Returns a CrossCat state.
    """
    # XXX: those should be outsourced util functions. This has the advantage for
    # us to document them.
    for k,v in schema.items():
        if v['type'].lower() == 'nominal':
            assert len(v['values']) > 1

    df_no_strings = replace_strings(df, schema)

    df_not_ignored = df_no_strings[[
        c for c in df_no_strings
        if not schema[c]['type'] == 'ignored'
    ]]

    col_name_id_mapping = {c : i for i,c in enumerate(df_not_ignored.columns)}

    cgpm_cc_types = replace(
            {'numerical': 'normal', 'nominal': 'categorical'},
            [schema[c]['type'] for c in df_not_ignored.columns]
    )
    cgpm_distargs = [
            None if schema[c]['type'].lower() == 'numerical'
            else {'k' : len(schema[c]['values'])}
            for c in df_not_ignored.columns
    ]
    for distarg in cgpm_distargs:
        assert (distarg is None) or ('k' in distarg)

    def make_state(i):
        return State(
            df_not_ignored.values,
            outputs=range(df_not_ignored.shape[1]),
            cctypes=cgpm_cc_types,
            distargs=cgpm_distargs,
            rng=gu.gen_rng(i + 1)
        )
    mapper =  parallel_map if parallel else map
    states = list(mapper(make_state, range(n_models)))
    return states, col_name_id_mapping


def cgpm_to_spn(states, col_name_id_mapping, schema):
    """Functoin to convert from the CGPM model represenation to SPN
    representatoin."""
    metadata_list = [state.to_metadata() for state in states]
    # Here, we follow @fsaad's conventions
    variable_mapping = {int(v):k for k,v in col_name_id_mapping.items()}
    # This needs to be a tuple as convert_states below makes this assumption.
    # We should probably keep it from making this assumption.
    categorical_mapping = [
            (v,[(i,cat) for cat,i in schema[k].get('values', {}).items()])
        for k,v in col_name_id_mapping.items()
    ]
    # `variables` is a dictionary mapping variable names to queryable variables.
    # `latests` is a dictionary mapping variable names to queryable latent cluster
    # variable.
    variables, latents, spn = convert_states(
        metadata_list,
        variable_mapping,
        categorical_mapping
    )
    # Inverting order of the three vars here to make the output more intuitive.
    # We should probably also fix this in convert_states.
    return spn, variables, latents


def make_inference(iters, columns=None, kernels=None):
    def inf(state):
        state.transition(N=iters, cols=columns, kernels=kernels)
        return state
    return inf


def cgpm_inference(
        states_in,
        col_name_id_mapping,
        iters=1,
        columns=None,
        kernels=None,
        parallel=True
    ):
    """Perform inference given a specified inference program"""
    mapper =  parallel_map if parallel else map
    states = deepcopy(states_in)
    cols = None if columns is None else [col_name_id_mapping[c] for c in columns]
    inf = make_inference(iters, columns=cols, kernels=kernels)
    states = list(mapper(inf, states))
    return states
