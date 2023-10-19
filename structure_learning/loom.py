import orjson
import click
import os
import numpy as np
import polars as pl

from structurelearningapi.create_model import create_model
from structurelearningapi.io import deserialize_column_models, serialize
from structurelearningapi.inference import gibbs_alpha, gibbs_view_alphas, gibbs_column_hypers

@click.command()
@click.option("--loom_folder")
@click.option("--data_filename", default="data/preprocessed.csv")
@click.option("--column_model_filename", default="data/column_models.json")
@click.option("--out_filename", default="data/cgpm/hydrated/sample.0.json")
def loom_to_cgpm(loom_folder, data_filename, column_model_filename, out_filename):
    model_filename = os.path.join(loom_folder, "model.json")
    assign_filename = os.path.join(loom_folder, "assign.json")

    df = pl.read_csv(data_filename)

    with open(model_filename, "rb") as f:
        model_metadata = orjson.loads(f.read())

    with open(assign_filename, "rb") as f:
        zrv = orjson.loads(f.read())
        zrv = {int(k): v for k, v in zrv.items()}

    with open(column_model_filename, "rb") as f:
        column_models = orjson.loads(f.read())
        column_models = deserialize_column_models(column_models)

    kinds = model_metadata["kinds"]

    zv = {dim_idx: view_idx for view_idx, view in enumerate(kinds)
     for dim_idx in view["featureids"]}


    model = create_model(
        df,
        column_models,
        zv,
        zrv
    )

    gibbs_alpha(model)
    gibbs_view_alphas(model)
    [gibbs_column_hypers(model) for _ in range(10)]

    metadata = serialize(model)

    with open(out_filename, "wb") as f:
        f.write(metadata)