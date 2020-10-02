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

def replace_strings(df_in, schema):
    """Replace categorical values in a dataframe with integers as specified in
    the schema."""
    df = df_in.copy()
    for c in df.columns:
        if schema[c]['type'].lower() == 'nominal':
            df[c] = df_in[c].replace(to_replace=schema[c]['values'])
    return df

def create_cgpm(df, schema, randseed=42):
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

    cgpm_cc_types = [
            'normal' if schema[c]['type'] == 'numerical' else 'categorical'
            for c in df_not_ignored.columns
    ]
    cgpm_distargs = [
            None if schema[c]['type'] == 'numerical'
            else {'k' : len(schema[c]['values'])}
            for c in df_not_ignored.columns
    ]
    for distarg in cgpm_distargs:
        assert (distarg is None) or ('k' in distarg)

    state = State(
        df_not_ignored.values,
        outputs=range(df_not_ignored.shape[1]),
        cctypes=cgpm_cc_types,
        distargs=cgpm_distargs,
        rng=gu.gen_rng(randseed)
    )
    return state, col_name_id_mapping
