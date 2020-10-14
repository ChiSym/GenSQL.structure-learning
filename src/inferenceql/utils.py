# Copyright 2020 MIT Probabilistic Computing Project.
# See LICENSE.txt
from cgpm.crosscat.state import State
from inferenceql.auto_modeling import cgpm_to_spn

import json
import os
import pandas as pd

def read_table(path):
    """Read a data table in csv form from disk."""
    assert path.endswith('.csv'), 'Need to supply a csv file'
    df = pd.read_csv(path)
    # Ensure boolean as read as strings
    for c in df.columns:
        if df[c].dtype == 'bool':
            df[c] = df[c].astype(object).apply(str)
    return df


def read_schema(path):
    """Read a schema file from disk."""
    assert path.endswith('.json'), 'Need to supply a json file'
    with open(path, 'r') as schema_f:
            schema = json.load(schema_f)
    return schema


def read_data(directory_path):
    """Read both data .csv and schema .json from disk."""
    df = read_table(os.path.join(directory_path, 'data.csv'))
    schema = read_schema(os.path.join(directory_path, 'schema.json'))
    return df, schema


def read_cgpms(directory_path, cgpm_name='cgpm'):
    """Read an ensemble of CGPM models from disk."""
    path = os.path.join(directory_path, '{}.json'.format(cgpm_name))
    with open(path, 'r') as f:
        saved_cgpm = json.load(f)
    assert 'suffstats' in saved_cgpm['metadata_list'][0].keys(), \
            '''Outdated version of CGPM is running; upgrade to 0.1.3.post1+g56a4818
             or higher'''
    states = [State.from_metadata(m) for m in saved_cgpm['metadata_list']]
    return  states, saved_cgpm['col_name_id_mapping']


def write_cgpms(states, col_name_id_mapping, directory_path, cgpm_name='cgpm'):
    """Write an ensemble of CGPM models to disk."""
    assert isinstance(states, list), 'States should be an ensemble (list) of CC states'
    assert isinstance(states[0], State)
    state_data_list = [state.to_metadata() for state in states]
    path = os.path.join(directory_path, '{}.json'.format(cgpm_name))
    with open(path, 'w') as f:
        json.dump({
            'metadata_list'       : state_data_list,     # The CGPM states.
            'col_name_id_mapping' : col_name_id_mapping, # map colname to index
        }, f)
    return path

def get_metadata(directory_path):
    """ Read what inference was run to with this model/data and other relevant metadata from the
    experiment."""
    metadata_path = os.path.join(directory_path, 'metadata.json')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
                metadata = json.load(f)
    else:
        metadata = {'Inference':[]}
    return metadata

def read_analysis(directory_path, cgpm_name='cgpm'):
    df, schema = read_data(directory_path)
    states, col_name_id_mapping = read_cgpms(
         directory_path,
         cgpm_name=cgpm_name
    )
    metadata = get_metadata(directory_path)
    analysis = {
        'data':df,
        'schema': schema,
        'states': states,
        'col_name_id_mapping': col_name_id_mapping,
        'metadata': metadata
    }
    return analysis


def write_analysis(states, col_name_id_mapping, directory_path, inf_meta_data):
    metadata = get_metadata(directory_path)
    metadata['Number of models in ensemble'] = len(states)
    metadata['Inference'].append(inf_meta_data)
    write_cgpms(states, col_name_id_mapping, directory_path, cgpm_name='cgpm')
    with open(os.path.join(directory_path, 'metadata.json'), 'w') as f:
        json.dump(metadata, f)

def read_spn(directory_path, cgpm_name='cgpm'):
    """Read an SPN from disk, given an ensemble of CrossCat models saved via
    CGPM machinery."""
    path = os.path.join(directory_path, '{}.json'.format(cgpm_name))
    schema = read_schema(os.path.join(directory_path, 'schema.json'))
    states, col_name_id_mapping = read_cgpms(directory_path, cgpm_name=cgpm_name)
    return cgpm_to_spn(states, col_name_id_mapping, schema)
