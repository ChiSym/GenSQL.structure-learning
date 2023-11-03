import statsmodels.formula.api as smf
from structure_learning.io import read_csv
from structurelearningapi.io import deserialize_column_models
from structurelearningapi.sample import conditional_sample
from structurelearningapi.create_model import wrapper
from structurelearningapi.model_attributes import logpdf
from sppl.compilers.spe_to_dict import spe_from_dict
from sppl.transforms import Id
from patsy import ModelDesc
from tqdm import tqdm
from sklearn.metrics import RocCurveDisplay

import json
import polars as pl
import numpy as np
import os
import orjson
import click

@click.command()
@click.option('--data', help='Path to the data file')
@click.option('--formula', help='Regression formula string')
@click.option('--column_model_filename', help='Column model filename')
@click.option('--model_filename', help='Model filename')
@click.option('--result_filename', help='Result filename')
def prediction(data, formula, model_filename, column_model_filename, result_filename):
    with open(column_model_filename, "rb") as f:
        column_models = orjson.loads(f.read())
        column_models = deserialize_column_models(column_models)

    df = read_csv(data, column_models)
    
    model = spe_from_dict(json.load(open(model_filename, "r")))

    expert_features = """
    menopausal_status + survival_status + recurrence_indicator + distant_recurrence_indicator
    + genetic_recurrence_score
    + age
    + age.cut([50, 65]) : genetic_recurrence_score
    + menopausal_status : genetic_recurrence_score
    """
    naive_feature_candidates = [
        col for col in df.columns
        if col not in ["endocrine_therapy_ai", "endocrine_therapy_tam", "endocrine_therapy_ofs"]]
    rng = np.random.default_rng(1234)
    naive_features = rng.choice(naive_feature_candidates, 3, replace=False)

    y = "outcome"
    expert_formula = f"{y} ~ {expert_features}"
    naive_formula = f"{y} ~ {' + '.join(naive_features)}"

    x, y = get_xy(expert_formula, df.columns)
    fill_df = fill_null(df, x)

    multi_df = fill_df.with_columns(
        categorical_outcome = pl.concat_str([
            pl.col("endocrine_therapy_ai"),
            pl.col("endocrine_therapy_tam"),
            pl.col("endocrine_therapy_ofs"),
        ], separator=" | ").cast(pl.Categorical),
    ).with_columns(
        outcome=pl.col("categorical_outcome").to_physical()
    )

    expert_yhat = get_linear_predictions(expert_formula, multi_df)
    naive_yhat = get_linear_predictions(naive_formula, multi_df)

    outcomes = multi_df['categorical_outcome'].cat.get_categories()
    endocrine_therapies = ["endocrine_therapy_ai", "endocrine_therapy_tam", "endocrine_therapy_ofs"]

    assignments = [
        {k: v for k, v in zip(endocrine_therapies, outcome.split(" | "))}
        for outcome in outcomes
    ]

    sppl_preds = get_lpm_predictions(
        df,
        [feat for feat in x if feat not in ["genetic_recurrence_score"]],
        assignments,
        model)

    sppl_yhat = np.exp(sppl_preds - np.logaddexp.reduce(sppl_preds, axis=1)[:, None])

    one_hot_outcome = np.zeros((len(multi_df["outcome"]), multi_df["outcome"].max() + 1))
    one_hot_outcome[np.arange(len(multi_df["outcome"])), multi_df['outcome']] = 1

    np.save("data/expert_yhat_endocrine.npy", expert_yhat)
    np.save("data/naive_yhat_endocrine.npy", naive_yhat)
    np.save("data/lpm_yhat_endocrine.npy", sppl_yhat)
    np.save("data/ground_trut_endocrine.npy", one_hot_outcome)

def fill_null(df, cols):
    for col in cols:
        if df[col].is_numeric():
            fill_val = df[col].median()
        else:
            fill_val = df[col].mode()[0]
        
        df = df.with_columns(
            pl.col(col).fill_null(fill_val)
        )

    return df

def rsquared(y, yhat):
    y_res = y - yhat
    return 1 - (y_res**2).sum() / ((y - y.mean())**2).sum()

def get_linear_predictions(formula, df):
    # lin_results = smf.logit(formula, data=df).fit(maxiter=100)
    # lin_results = smf.ols(formula, data=df).fit()
    lin_results = smf.mnlogit(formula, data=df).fit(method="bfgs", maxiter=1000)
    return lin_results.predict()

def get_lpm_predictions(df, x, assignments, model):
    logps = np.zeros((len(df), len(assignments)))
    assignments = [dict_to_sppl_sample(assignment) for assignment in assignments]

    for i, row in tqdm(enumerate(df.to_dicts())):
        X = {k: v for k, v in row.items() if (k in x) and (v is not None)}
        X = dict_to_sppl_sample(X)

        cspe = model.constrain(X)
        logp_row = [cspe.logpdf(assignment) for assignment in assignments]
        logps[i, :] = logp_row

    return logps

def get_lpm_predictions_continuous(df, x, y, model):
    mus = np.zeros(len(df))

    for i, row in tqdm(enumerate(df.to_dicts())):
        X = {k: v for k, v in row.items() if (k in x) and (v is not None) }
        X = dict_to_sppl_sample(X)
        cspe = model.constrain(X)
        samples = cspe.sample(1000)

        mus[i] = np.mean([sample[Id(y)] for sample in samples])

    return mus



def get_xy(formula, column_names):
    desc = ModelDesc.from_formula(formula)
    y = desc.lhs_termlist[0].name()

    factor_names = [
        factor.name() 
        for term in desc.rhs_termlist
        for factor in term.factors
    ]

    column_factors = [
        largest_match(factor_name, column_names)
        for factor_name in factor_names
    ]

    return list(set(column_factors)), y

def largest_match(factor_name: str, column_names: list[str]):
    matches = [column_name for column_name in column_names if column_name in factor_name]
    if len(matches) == 0:
        raise ValueError(f"Factor {factor_name} not found in column names")
    return max(matches, key=len)

def dict_to_sppl_sample(dict):
    return {Id(k): v for k, v in dict.items()}