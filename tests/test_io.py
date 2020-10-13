# Copyright 2020 MIT Probabilistic Computing Project.
# See LICENSE.txt
from cgpm.crosscat.state import State
from inferenceql.auto_modeling import create_cgpms
from inferenceql.utils import read_analysis
from inferenceql.utils import read_cgpms
from inferenceql.utils import read_data
from inferenceql.utils import read_spn
from inferenceql.utils import write_cgpms
from inferenceql.utils import write_analysis

import json
import os
import pandas as pd
import pytest

def _get_test_df():
    return pd.DataFrame({
            'key' : [0, 1, 2, 3],
            'a'   : [1.2, 9.3, 10.1, 12.],
            'b'   : [2.2, 1.3, 11.1, 1.],
            'c'   : ['True', 'False', 'True', 'False'],
        })


def _get_test_schema():
    return {
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


@pytest.fixture
def get_test_states():
    return create_cgpms(
        _get_test_df(),
        _get_test_schema(),
        n_models=3,
        parallel=False
    )


@pytest.fixture
def tmp_analysis_dir(tmpdir):
    """Make a test directory for an analysis."""
    df = _get_test_df()
    schema = _get_test_schema()
    # Write the files to disk.
    df.to_csv(os.path.join(tmpdir, 'data.csv'), index=False)
    with open(os.path.join(tmpdir, 'schema.json'), 'w') as schema_f:
            json.dump(schema, schema_f)
    return df, schema, tmpdir


def test_read_data(tmp_analysis_dir):
    df_written, schema_written, test_dir = tmp_analysis_dir
    df_read, schema_read = read_data(test_dir)
    assert df_read.equals(df_written)
    assert  schema_read == schema_written


def test_write_cgpm(tmpdir, get_test_states):
    states, col_name_id_mapping = get_test_states
    write_cgpms(states, col_name_id_mapping, tmpdir)


def test_read_cgpm(tmpdir, get_test_states):
    states_in, col_name_id_mapping_in = get_test_states
    write_cgpms(states_in, col_name_id_mapping_in, tmpdir)

    states_out, col_name_id_mapping_out = read_cgpms(tmpdir, cgpm_name='cgpm')

    assert col_name_id_mapping_out, col_name_id_mapping_in
    for i in range(len(states_in)):
        assert states_out[i].to_metadata() == states_in[i].to_metadata()
        assert states_out[i].logpdf(None, {2:1}, {0:-1}) == states_in[i].logpdf(None, {2:1}, {0:-1})


def assert_analysis_format(analysis):
    assert isinstance(analysis['data'], pd.DataFrame)
    assert isinstance(analysis['schema'], dict)
    assert isinstance(analysis['states'], list)
    assert isinstance(analysis['states'][0], State)
    assert isinstance(analysis['col_name_id_mapping'], dict)
    assert isinstance(analysis['metadata'], dict)

def test_read_analysis(tmp_analysis_dir, get_test_states):
    _,  _, test_dir = tmp_analysis_dir
    states_in, col_name_id_mapping_in = get_test_states
    write_cgpms(states_in, col_name_id_mapping_in, test_dir)

    analysis = read_analysis(test_dir)
    assert_analysis_format(analysis)


def test_write_analysis(tmp_analysis_dir, get_test_states):
    _,  _, test_dir = tmp_analysis_dir
    states, col_name_id_mapping = get_test_states
    write_analysis(
        states,
        col_name_id_mapping,
        test_dir,
        {
            'foo_infernce_iterations': 3,
            'bar_infernce_iterations': 4,
        }
    )
    analysis = read_analysis(test_dir)
    assert_analysis_format(analysis)
    assert analysis['metadata']['Inference'][0]['foo_infernce_iterations'] == 3
    assert analysis['metadata']['Inference'][0]['bar_infernce_iterations'] == 4


def test_read_spn(tmp_analysis_dir, get_test_states):
    _,  _, test_dir = tmp_analysis_dir
    states, col_name_id_mapping = get_test_states
    write_cgpms(states, col_name_id_mapping, test_dir)
    spn, variables, latents = read_spn(test_dir)
    n_samples = 3
    samples = spn.sample_subset([variables['a'], variables['c']], N=n_samples)
    assert len(samples) == n_samples
    assert len(samples[0]) == 2
