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

TEST_DIR = 'analyses/test'

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


def _get_test_states():
    return create_cgpms(
        _get_test_df(),
        _get_test_schema(),
        n_models=3,
        parallel=False
    )

def _make_analysis_dir(path=TEST_DIR):
    """Make a test directory for an analysis."""
    df = _get_test_df()
    schema = _get_test_schema()
    # I am unclear of the exist_ok flag should be set. From a CI testing
    # perpective it should not be set. From a test driven development
    # perspective it should be set. os.makedirs(TEST_DIR, exist_ok=True)
    os.makedirs(TEST_DIR)
    # Write the files to disk.
    df.to_csv(os.path.join(TEST_DIR, 'data.csv'), index=False)
    with open(os.path.join(TEST_DIR, 'schema.json'), 'w') as schema_f:
            json.dump(schema, schema_f)
    return df, schema

def _remove_if_exists(path):
    if os.path.exists(path):
        os.remove(path)

def _clean_test_dir():
    """Remove a test directory for an analysis. We avoid using shutil.rmtree()
    here in order to avoid accidentally deleting wort."""
    _remove_if_exists(os.path.join(TEST_DIR, 'schema.json'))
    _remove_if_exists(os.path.join(TEST_DIR, 'data.csv'))
    _remove_if_exists(os.path.join(TEST_DIR, 'cgpm.json'))
    _remove_if_exists(os.path.join(TEST_DIR, 'metadata.json'))
    os.rmdir(TEST_DIR)


def test_read_data():
    df_written, schema_written = _make_analysis_dir()
    df_read, schema_read = read_data(TEST_DIR)
    assert df_read.equals(df_written)
    assert  schema_read == schema_written
    _clean_test_dir()


def test_write_cgpm():
    states, col_name_id_mapping = _get_test_states()
    os.makedirs(TEST_DIR)
    write_cgpms(states, col_name_id_mapping, TEST_DIR)
    _clean_test_dir()


def test_read_cgpm():
    states_in, col_name_id_mapping_in = _get_test_states()
    os.makedirs(TEST_DIR)
    write_cgpms(states_in, col_name_id_mapping_in, TEST_DIR)

    states_out, col_name_id_mapping_out = read_cgpms(TEST_DIR, cgpm_name='cgpm')

    _clean_test_dir()

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

def test_read_analysis():
    _make_analysis_dir()
    states_in, col_name_id_mapping_in = _get_test_states()
    write_cgpms(states_in, col_name_id_mapping_in, TEST_DIR)

    analysis = read_analysis(TEST_DIR)
    assert_analysis_format(analysis)

    _clean_test_dir()

def test_write_analysis():
    _make_analysis_dir()
    states, col_name_id_mapping = _get_test_states()
    write_analysis(
        states,
        col_name_id_mapping,
        TEST_DIR,
        {
            'foo_infernce_iterations': 3,
            'bar_infernce_iterations': 4,
        }
    )
    analysis = read_analysis(TEST_DIR)
    assert_analysis_format(analysis)
    assert analysis['metadata']['Inference'][0]['foo_infernce_iterations'] == 3
    assert analysis['metadata']['Inference'][0]['bar_infernce_iterations'] == 4

    _clean_test_dir()

def test_read_spn():
    _make_analysis_dir()
    states, col_name_id_mapping = _get_test_states()
    write_cgpms(states, col_name_id_mapping, TEST_DIR)
    spn, variables, latents = read_spn(TEST_DIR)
    n_samples = 3
    samples = spn.sample_subset([variables['a'], variables['c']], N=n_samples)
    assert len(samples) == n_samples
    assert len(samples[0]) == 2

    _clean_test_dir()
