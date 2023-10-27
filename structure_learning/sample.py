import click
import os
import polars as pl

from structurelearningapi.sample import sample
from structurelearningapi.io import deserialize
from structurelearningapi.create_model import make_cgpm
from structurelearningapi.cgpm_wrapper import CGPMWrapper

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
        get_wrapper(metadata, df)
        for metadata in metadatas
    ]

    sample_list = [
        sample(wrapper, sample_count//n_models)
        for wrapper in wrappers]

    sample_df = pl.concat(sample_list)
    sample_df.write_csv(output)

def get_wrapper(metadata, df):
    cgpm = make_cgpm(
        df, 
        metadata.crosscat,
        metadata.column_models, 
        metadata.constraints
    )

    return CGPMWrapper(
        cgpm,
        df,
        metadata.column_models, 
        metadata.constraints
    )