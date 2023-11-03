import click
import os
import polars as pl
import json
from sppl.compilers.spe_to_dict import spe_to_dict

from structurelearningapi.io import deserialize
from structurelearningapi.create_model import wrapper
from structurelearningapi.sppl import sppl


@click.command()
@click.option('--model_dir', help='Path to the model directory')
@click.option('--data', help='Path to the data directory')
@click.option('--output', help='Path to the output file')
def cgpm_to_sppl(model_dir, output, data):
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

    sppl_model = sppl(wrappers)
    serial_sppl = spe_to_dict(sppl_model)

    os.makedirs(os.path.dirname(output), exist_ok=True)

    with open(output, "w") as f:
        json.dump(serial_sppl, f)