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
from inferenceql.utils import read_analysis
from inferenceql.utils import read_data
from inferenceql.utils import write_analysis

import argparse
import os

def retrieve_analysis(kwargs):
   assert os.path.exists(os.path.join(kwargs['analysis'], 'data.csv')), \
           'Analysis path does not contain a file data.csv'
   assert os.path.exists(os.path.join(kwargs['analysis'], 'schema.json')), \
           'Analysis path does not contain a file schema.json'

   cgpm_path = os.path.join(
           kwargs['analysis'],
           '{}.json'.format(kwargs['name'])
   )

   if os.path.exists(cgpm_path):
       print('Loading models from disk. This can take while...')
       print('... done')
       analysis = read_analysis(kwargs['analysis'])
       assert len(analysis['states']) == kwargs['models'], \
               'The intended number of models specified via CLI differed from what was on disk'
   else:
       print('Initializing models. This can take while...')
       df, schema = read_data(kwargs['analysis'])
       states, col_name_id_mapping = create_cgpms(
               df,
               schema,
               n_models=kwargs['models'],
               parallel=kwargs['parallel']
       )
       print('... done')
       analysis = {
           'data':df,
           'schema': schema,
           'states': states,
           'col_name_id_mapping': col_name_id_mapping,
           'metadata': {'inference':[]}
       }
   return analysis

def run_automodeling(kwargs):
    analysis = retrieve_analysis(kwargs)
    states = cgpm_inference(
        analysis['states'],
        analysis['col_name_id_mapping'],
        iters=kwargs['iterations'],
        columns=kwargs['columns'],
        kernels=kwargs['kernels'],
        parallel=kwargs['parallel']
    )
    inf_metadata = {
        'iters':kwargs['iterations'],
        'kernels':kwargs['kernels'],
    }
    write_analysis(
        states,
        analysis['col_name_id_mapping'],
        kwargs['analysis'],
        inf_metadata
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Run automated modeling pipeline'
    )

    parser.add_argument(
        '-a', '--analysis',
        required=True,
        type=str,
        help='Path to a directory containing an analysis'
    )
    parser.add_argument(
        '-i', '--iterations',
        type=int,
        default=0,
        help='Number of Iterations to be run with the kernels, specified below.'
    )
    parser.add_argument(
        '-p', '--parallel',
        action='store_true',
        default=False,
        help='Run CPGPM inference in parallel for each model/state.'
    )
    parser.add_argument(
        '-k', '--kernels',
        nargs='+',
        type=str,
        default=['alpha', 'view_alphas', 'column_hypers', 'rows', 'columns'],
        help='Gibbs kernels to be run.'
    )
    parser.add_argument(
        '-m', '--models',
        type=int,
        default=1,
        help='Number of models in the ensemble'
    )
    parser.add_argument(
        '-c', '--columns',
        nargs='+',
        type=str,
        default=None,
        help='Consider only the specified subset of columns'
    )
    parser.add_argument(
        '-n', '--name',
        type=str,
        default='cgpm',
        help='Name under which to safe/look for the CGPM model'
    )
    args = parser.parse_args()
    if (len(args.kernels) < 5) and ('rows' in args.kernels):
        raise ValueError(
            'Suppling a subset of kernels including the "rows" kernel is currently buggy. Other subset of kernels should work.')
    print(vars(args))
    run_automodeling(vars(args))
