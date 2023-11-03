import click
import os
import polars as pl
import numpy as np
import json

from sppl.compilers.spe_to_dict import spe_from_dict
from scipy.special import logsumexp
from structurelearningapi.sample import sample
from structurelearningapi.io import deserialize
from structurelearningapi.create_model import wrapper

@click.command()
@click.option('--sample_count', type=int, help='Number of samples to draw')
@click.option('--model_dir', help='Path to the model directory')
@click.option('--data', help='Path to the data directory')
@click.option('--output', help='Path to the output file')
def sample_cgpm(sample_count, model_dir, output, data):
    sample_filenames = os.listdir(model_dir)
    n_models = len(sample_filenames)

    metadatas = [deserialize(
            os.path.join(model_dir, sample_filename))
        for sample_filename in sample_filenames]

    column_models = metadatas[0].column_models

    df = pl.read_csv(
        data, 
        dtypes={
            cm.name: pl.Utf8 if cm.distribution == "categorical" else pl.Float64
            for cm in column_models
        }
    )

    wrappers = [
        wrapper(metadata, df)
        for metadata in metadatas
    ]

    k_list = np.random.multinomial(sample_count, np.ones(len(wrappers))/ len(wrappers))
    sample_list = [
        sample(wrapper, k)
        for k, wrapper in zip(k_list, wrappers)
    ]

    sample_df = pl.concat(sample_list)

    sample_df.write_csv(output)

@click.command()
@click.option('--sample_count', type=int, help='Number of samples to draw')
@click.option('--model', help='Path to the model')
@click.option('--data', help='Path to the data directory')
@click.option('--output', help='Path to the output file')
def sppl_sample(sample_count, model, output, data):
    spe = spe_from_dict(json.load(open(model, "r")))
    spe_samples = spe.sample(sample_count)
    spe_samples = [sppl_sample_to_dict(sample) for sample in spe_samples]
    df = pl.from_dicts(spe_samples)

    df.write_csv(output)

def sppl_sample_to_dict(sample):
    return {k.token: v for k, v in sample.items()}
