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

import json
import pandas as pd
import pytest

@pytest.mark.parametrize('parallel', [True, False])
def test_smoke_create_cgpms(parallel):
    schema = {
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
    df = pd.DataFrame({
        'key' : [0, 1, 2, 3],
        'a'   : [1.2, 9.3, 10.1, 12.],
        'b'   : [2.2, 1.3, 11.1, 1.],
        'c'   : ['True', 'False', 'True', 'False'],
    })
    n_models = 3

    states, col_name_id_mapping = create_cgpms(
        df,
        schema,
        n_models=n_models,
        parallel=parallel
    )

    assert len(states) == 3

    assert set(col_name_id_mapping.keys()) == set(['a', 'b', 'c'])

    lpdf1 = states[n_models-1].logpdf(None, {2:1}, {0:-1})
    lpdf2 = states[0].logpdf(None, {2:1}, {0:-1})
    assert isinstance(lpdf1, float)
    assert isinstance(lpdf2, float)

    assert lpdf1 != lpdf2, 'Something is wrong with random initialization'
    # Once again. Just to be sure.
    assert states[0].alpha() != states[1].alpha(), 'Something is wrong with random initialization'
