import click
import os
import polars as pl
import numpy as np
import json
import pickle
import orjson

from sppl.compilers.spe_to_dict import spe_from_dict
from scipy.special import logsumexp
from structurelearningapi.sample import sample
from structurelearningapi.io import deserialize
from structurelearningapi.create_model import wrapper

@click.command()
@click.option('--sample_count', type=int, help='Number of samples to draw')
@click.option('--cgpm-model', help='Model name')
@click.option('--data', help='Path to the data directory')
def sample_cgpm(sample_count, cgpm_model, data):
    model_dir = f"data/cgpm/{cgpm_model}"
    sample_filenames = os.listdir(model_dir)

    metadatas = [deserialize(
            os.path.join(model_dir, sample_filename))
        for sample_filename in sample_filenames]

    df = pl.read_parquet(data)

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

    sample_df.write_csv(f"data/synthetic-data-cgpm-{cgpm_model}.csv")
    sample_df.write_parquet(f"data/synthetic-data-cgpm-{cgpm_model}.parquet")

@click.command()
@click.option('--sample_count', type=int, help='Number of samples to draw')
@click.option('--model', help='Path to the model')
@click.option('--output', help='Path to the output file')
def sppl_sample(sample_count, model, output):
    spe = spe_from_dict(json.load(open(model, "r")))
    spe_samples = spe.sample(sample_count)
    spe_samples = [sppl_sample_to_dict(sample) for sample in spe_samples]
    df = pl.from_dicts(spe_samples)

    df.write_csv(output)
    df.write_parquet(output.replace(".csv", ".parquet"))

def sppl_sample_to_dict(sample):
    return {k.token: v for k, v in sample.items()}

@click.command()
@click.option('--filename', help='Path to the data directory')
@click.option('--column_models', help='Path to the column models file.')
def csv_to_parquet(filename, column_models):
    with open(column_models, 'rb') as f:
        column_models = orjson.loads(f.read())
    dtypes={
        cm["name"]: pl.Utf8 if cm["distribution"] == "categorical" else pl.Float64
        for cm in column_models
        }
    df = pl.read_csv(filename, dtypes=dtypes)
    df.write_parquet(filename.replace(".csv", ".parquet"))

@click.command()
@click.option('--sample_count', type=int, help='Number of samples to draw')
@click.option('--model', help='Path to the model')
def sample_baseline(model, sample_count):
    model_path = "data/{}.pkl".format(model)
    synthesizer = pickle.load(open(model_path, "rb"))
    synthetic_data = synthesizer.sample(num_rows=sample_count)
    synthetic_data_path = f"data/synthetic-data-{model}"

    synthetic_data = pl.from_pandas(synthetic_data)
    synthetic_data.write_csv(synthetic_data_path + ".csv")
    synthetic_data.write_parquet(synthetic_data_path + ".parquet")