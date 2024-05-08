import click
import polars as pl
import orjson
import os
import itertools
from lpm_fidelity.distances import bivariate_distance, univariate_distance

@click.command()
@click.option('--real_data', help='Path to the real data file')
@click.option('--model', help='Name of the model to be evaluated')
def marginal_fits(real_data, model):
    count_thresh = 100

    synthetic_data_path = f"data/discretized-synthetic-data-{model}.parquet"
    synthetic_df = pl.read_parquet(synthetic_data_path)
    real_df = pl.read_parquet(real_data)

    uni_dists = {"Column": [], "Score": []}
    bi_dists = {"Column 1": [], "Column 2": [], "Score": []}
    distance_metric = "kl"

    all_cols = real_df.columns
    for col_name in all_cols: 
        filtered_df = real_df[[col_name]].drop_nulls()
        if len(filtered_df) < count_thresh: 
            continue
        col_real = filtered_df[col_name]
        col_synth = synthetic_df[col_name]
        try:
            dist = univariate_distance(col_synth, col_real, distance_metric=distance_metric)
        except AssertionError:
            import ipdb; ipdb.set_trace()
        uni_dists["Column"].append(col_name)
        uni_dists["Score"].append(dist)
    
    col_pairs = list(itertools.combinations(all_cols, 2)) 

    for col1, col2 in col_pairs: 
        # count the number of rows where real_df has non-null (polar's) between the columns
        filtered_df = real_df[[col1, col2]].drop_nulls()
        if len(filtered_df) < count_thresh: 
            continue
        dist = bivariate_distance(filtered_df[col1], filtered_df[col2], synthetic_df[col1], synthetic_df[col2], distance_metric=distance_metric) 
        bi_dists["Column 1"].append(col1)
        bi_dists["Column 2"].append(col2) 
        bi_dists["Score"].append(dist)

    dists = {"1d": uni_dists, "2d": bi_dists}
    dist_dfs = {dims: pl.from_dict(dist_dict) for dims, dist_dict in dists.items()}
    for dims, dist_df in dist_dfs.items(): 
        dist_df = dist_df.sort("Score")
        dist_df = dist_df.with_columns(
            idx=pl.arange(0, dist_df.shape[0]),
            model=pl.repeat(model, dist_df.shape[0]),
        )
        dist_dfs[dims] = dist_df
        dist_df.write_csv(f"qc/marginals/{model}_{dims}_fits.csv")
    
    # we still need to plot the marginal fits


@click.command()
@click.option('--model', '-m', multiple=True)
def marginal_fits_plot(model):
    paths_1d_fit = [f"qc/marginals/{m}_1d_fits.csv" for m in model]
    dfs_1d_fit = [pl.read_csv(path) for path in paths_1d_fit]
    dfs_1d_fit = [preprocess_1d_fits(df, m) 
        for df, m in zip(dfs_1d_fit, model)]

    pl.concat(dfs_1d_fit).write_csv("qc/marginals/1d_fits.csv")

    paths_2d_fit = [f"qc/marginals/{m}_2d_fits.csv" for m in model]
    dfs_2d_fit = [pl.read_csv(path) for path in paths_2d_fit]
    dfs_2d_fit = [preprocess_2d_fits(df, m) 
        for df, m in zip(dfs_2d_fit, model)]

    pl.concat(dfs_2d_fit).write_csv("qc/marginals/2d_fits.csv")


def preprocess_1d_fits(df, model):
    return df[["Column", "Score"]].with_columns(
        idx=pl.arange(0, df.shape[0]),
        model=pl.repeat(model, df.shape[0]),
    )

def preprocess_2d_fits(df, model):
    return df[["Column 1", "Column 2", "Score"]].with_columns(
        idx=pl.arange(0, df.shape[0]),
        model=pl.repeat(model, df.shape[0]),
    )