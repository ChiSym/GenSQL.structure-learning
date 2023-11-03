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

    infer_logs = [
        json.load(open(os.path.join(f"loom/samples/sample.{i}/infer_log.json")))
        for i in range(n_models)
    ]
    scores = np.array([
        infer_log["args"]["scores"]["score"] 
        for infer_log in infer_logs])
    ps = np.exp(scores - logsumexp(scores))

    sample_list = [
        sample(wrapper, int(sample_count * ps[i]))
        for i, wrapper in enumerate(wrappers)
        if ps[i] > 0]

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

def dict_to_sppl_sample(dict):
    return {Id(k): v for k, v in dict.items()}