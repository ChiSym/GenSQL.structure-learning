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
    states = cgpm_inference(
            STATES_INIT,
            COL_NAME_ID_MAPPING,
            iters=3,
            parallel=parallel
    )
    assert states[0].logpdf_score() != STATES_INIT[0].logpdf_score()

def test_consistency_parallel():
    states_serial = cgpm_inference(
            STATES_INIT,
            COL_NAME_ID_MAPPING,
            iters=3,
            parallel=False
    )
    states_parallel = cgpm_inference(
            STATES_INIT,
            COL_NAME_ID_MAPPING,
            iters=3,
            parallel=True
    )
    assert states_serial[0].logpdf_score() == states_parallel[0].logpdf_score()
    assert states_serial[1].logpdf_score() == states_parallel[1].logpdf_score()

@pytest.mark.parametrize('parallel', PARALLEL)
def test_smoke_column_hypers_all_columns(parallel):
    states = cgpm_inference(
            STATES_INIT,
            COL_NAME_ID_MAPPING,
            iters=3,
            parallel=parallel,
            kernels=['column_hypers']
    )
    assert states[0].dim_for(0).hypers != STATES_INIT[0].dim_for(0).hypers
    assert states[1].dim_for(0).hypers != STATES_INIT[1].dim_for(0).hypers
    assert states[0].alpha() == STATES_INIT[0].alpha()

@pytest.mark.parametrize('parallel', PARALLEL)
def test_smoke_column_hypers_specificy_columns(parallel):
    states = cgpm_inference(
            STATES_INIT,
            COL_NAME_ID_MAPPING,
            iters=3,
            parallel=parallel,
            kernels=['column_hypers'],
            columns=['a']
    )
    # Column 'a' corresponds to col index 0 -- thus dim_for[0]
    assert states[0].dim_for(0).hypers != STATES_INIT[0].dim_for(0).hypers
    assert states[0].dim_for(1).hypers == STATES_INIT[0].dim_for(1).hypers
