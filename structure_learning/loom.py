import orjson
import click
import os
import polars as pl
import gzip

from structurelearningapi.create_model import create_model
from structurelearningapi.io import deserialize_column_models, serialize

@click.command()
@click.option("--loom_folder")
@click.option("--data_filename", default="data/preprocessed.csv")
@click.option("--column_model_filename", default="data/column_models.json")
@click.option("--out_filename", default="data/cgpm/hydrated/sample.0.json")
def loom_to_cgpm(loom_folder, data_filename, column_model_filename, out_filename):
    model_filename = os.path.join(loom_folder, "model.json")
    assign_filename = os.path.join(loom_folder, "assign.json")

    df = pl.read_csv(data_filename)


    with gzip.open('loom/ingest/encoding.json.gz', 'rb') as f:
        encoding_str = f.read()
        encoding = orjson.loads(encoding_str)

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

    hypers_dict = {
        k: v for kind in kinds
        for k, v in get_kind_column_hypers(kind, column_models, encoding).items() }
    hypers_dict = {
        dim_idx_loom_to_column_model(k, column_models, encoding): v
        for k, v in hypers_dict.items()
    }
    hypers_list = [hypers_dict[idx] for idx in range(len(hypers_dict))]

    alpha = convert_alpha(model_metadata["topology"])
    view_alphas = {
        idx: convert_alpha(kind["product_model"]["clustering"])
        for idx, kind in enumerate(kinds)
    }

    model = create_model(
        df,
        column_models,
        zv,
        zrv,
        hypers_list,
        alpha,
        view_alphas
    )

    metadata = serialize(model)

    with open(out_filename, "wb") as f:
        f.write(metadata)


def get_kind_column_hypers(kind, column_models, encoding):
    categorical_hypers = kind['product_model'].get('dd', [])
    normal_hypers = kind['product_model'].get('nich', [])

    n_categorical = len(categorical_hypers)

    categorical_dim_idxs = kind['featureids'][:n_categorical]
    normal_dim_idxs = kind['featureids'][n_categorical:]

    hypers = convert_dirichlet_dims(categorical_hypers, categorical_dim_idxs, column_models, encoding) + convert_nich_dims(normal_hypers, normal_dim_idxs)
    
    return {idx: hyper for idx, hyper in zip(kind["featureids"], hypers)}


def convert_alpha(hypers: dict[str, float]):
    return {
        "alpha": hypers["alpha"],
        "discount": hypers["d"]
    }

def convert_dirichlet_dims(hypers: list[dict[str, list[float]]], dim_idxs, column_models, encoding):
    return [convert_dirichlet_dim(
        d, 
        [cm for cm in column_models if cm.name == encoding[dim_idx]['name']][0],
        encoding[dim_idx]
        ) for dim_idx, d in zip(dim_idxs, hypers)]


def convert_dirichlet_dim(hypers: dict[str, list[float]], column_model, encoding):
    alphas = {f'alpha_{idx_loom_to_column_model(i, column_model, encoding)}': v for i, v in enumerate(hypers['alphas'])}

    return alphas

def dim_idx_loom_to_column_model(idx, column_models, encodings):
    dim_name = encodings[idx]['name']
    return [i for i, cm in enumerate(column_models) if cm.name == dim_name][0]

def idx_loom_to_column_model(idx, column_model, class_encoding):
    assert class_encoding['name'] == column_model.name
    class_name = [k for k, v in class_encoding['symbols'].items() if v == idx][0]
    return column_model.categories.index(class_name)

def convert_nich_dims(hypers: list[dict[str, list[float]]], normal_dim_idxs):
    return [convert_nich_dim(d) for d in hypers]

def convert_nich_dim(hypers: dict[str, list[float]]):
    # loom and cgpm use different naming conventions,
    # but they both use the normal-inverse chi2 parametrization 
    # loom uses the more standard naming convention, as described on 
    # page 11 here:
    # https://www.cs.ubc.ca/~murphyk/Papers/bayesGauss.pdf

    return {
        "m": hypers["mu"],
        "r": hypers["kappa"],
        "nu": hypers["nu"],
        "s": hypers["sigmasq"]
    }