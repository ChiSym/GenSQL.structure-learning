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
from inferenceql.auto_modeling import create_cgpms
from inferenceql.auto_modeling import cgpm_inference
from spn.spn import SumSPN
import json
import pandas as pd
import pytest


SCHEMA = {
    'key': {
        'type' : 'ignored'
        },
    'a': {
        'type' : 'numerical'
        },
    'b': {
        'type' : 'numerical'
        },
    'c': {
        'type' : 'nominal',
        'values': {'False': 0, 'True': 1}
    }
}
DF = pd.DataFrame({
    'key' : [0, 1, 2, 3],
    'a'   : [1.2, 9.3, 10.1, 12.],
    'b'   : [2.2, 1.3, 11.1, 1.],
    'c'   : ['True', 'False', 'True', 'False'],
})

STATES_INIT, COL_NAME_ID_MAPPING = create_cgpms(
    DF,
    SCHEMA,
    n_models=2,
    parallel=True
)


PARALLEL = [True, False]


@pytest.mark.parametrize('parallel', PARALLEL)
def test_smoke_full_sweep(parallel):
    inf_prog = [{'REPEAT': 3, 'BODY':'default'}]
    states = cgpm_inference(
            STATES_INIT,
            COL_NAME_ID_MAPPING,
            inf_prog,
            parallel
    )
    assert states[0].logpdf_score() != STATES_INIT[0].logpdf_score()

def test_consistency_parallel():
    inf_prog = [{'REPEAT': 3, 'BODY':'default'}]
    states_serial = cgpm_inference(
            STATES_INIT,
            COL_NAME_ID_MAPPING,
            inf_prog,
            parallel=False
    )
    states_parallel = cgpm_inference(
            STATES_INIT,
            COL_NAME_ID_MAPPING,
            inf_prog,
            parallel=True
    )
    assert states_serial[0].logpdf_score() == states_parallel[0].logpdf_score()

@pytest.mark.parametrize('parallel', PARALLEL)
def test_smoke_column_hypers(parallel):
    inf_prog = [{'REPEAT': 2, 'BODY': {'GIBBS_COLUMN_HYPERS': 'default'}}]

    states = cgpm_inference(
            STATES_INIT,
            COL_NAME_ID_MAPPING,
            inf_prog,
            parallel
    )
    assert states[0].views[0].dims[0].hypers != STATES_INIT[0].views[0].dims[0].hypers
    assert states[0].alpha() ==STATES_INIT[0].alpha()

#def test_smoke_gibbs_inference():
#
#    inf_prog_1 = [
#            {'REPEAT': 3, 'BODY':'default'}
#    ]
#    inf_prog_2 = [
#            {'REPEAT': 3, 'BODY': 'default'},
#            {'REPEAT': 2, 'BODY': [{'GIBBS_COLUMN_HYPERS': 'default'}]}
#    ]
#    inf_prog_3 = [
#            {'REPEAT': 2, 'BODY': [
#                {'GIBBS_COLUMN_ALPHA': 'default'}
#            ]},
#            {'REPEAT': 2, 'BODY': [
#                {'GIBBS_COLUMN_HYPERS': {'COLUMNS': ['a', 'c']}}
#            ]}
#    ]
#    inf_prog_4 = [
#            {'REPEAT': 2, 'BODY': [
#                {'GIBBS_ROW_ASSIGNMETS': {'ROWS': [0]}}
#            ]}
#    ]
#
#    states_init, col_name_id_mapping = create_cgpms(
#        DF,
#        SCHEMA,
#        n_models=2,
#        parallel=parallel
#    )
#    states_1 = cgpm_gibbs_inference(states_init, col_name_id_mapping, inf_prog_1)
#
#    states_2 = cgpm_gibbs_inference(states_init, col_name_id_mapping, inf_prog_2)
#
#    states_3 = cgpm_gibbs_inference(states_init, col_name_id_mapping, inf_prog_3)
#    # Those have to get better.
#    assert states_1[0].view_alphas != states_init[0].view_alphas
#    assert states_2[0].view_alphas != states_init[0].view_alphas
#    assert states_3[0].view_alphas == states_init[0].view_alphas

# TODO: simple SMC.

