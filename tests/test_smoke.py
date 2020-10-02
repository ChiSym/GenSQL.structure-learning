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
from inferenceql.auto_modeling import create_cgpm

import json
import pandas as pd


def test_smoke_create_cgpm():
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
    state, col_name_id_mapping = create_cgpm(df, schema)

    assert list(col_name_id_mapping.keys()) == ['a', 'b', 'c']

    lpdf = state.logpdf(None, {2:1}, {0:-1})
    assert isinstance(lpdf, float)
