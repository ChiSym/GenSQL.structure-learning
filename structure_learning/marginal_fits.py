import click
import polars as pl
import orjson
import plotly
from sdv.metadata import SingleTableMetadata
from sdmetrics.reports.single_table import QualityReport
from sdmetrics.reports import utils


@click.command()
@click.option('--real_data', help='Path to the real data file')
@click.option('--column_models', help='Path to the column models file')
@click.option('--model', help='Name of the model to be evaluated')
def marginal_fits(real_data, model, column_models):
    with open(column_models, "rb") as f:
        column_models = orjson.loads(f.read())

    synthetic_data_path = f"data/synthetic-data-{model}.csv"

    synthetic_df = pl.read_csv(
        synthetic_data_path,
        dtypes={
            cm["name"]: pl.Utf8 
                if cm["distribution"] == "categorical" 
                else pl.Float64
            for cm in column_models
        }
    )

    real_df = pl.read_csv(real_data, dtypes=synthetic_df.schema)

    synthetic_df, real_df = synthetic_df.to_pandas(), real_df.to_pandas()

    # should we be using mapping table instead?
    metadata_obj = SingleTableMetadata()
    metadata_obj.detect_from_dataframe(real_df)
    metadata = metadata_obj.to_dict()

    report = QualityReport()
    report.generate(real_df, synthetic_df, metadata)

    marginal_fits_1d = report.get_details(property_name="Column Shapes").sort_values(
        "Score"
    ).reset_index(drop=True)
    marginal_fits_2d = report.get_details(
        property_name="Column Pair Trends"
    ).sort_values("Score").reset_index(drop=True)

    marginal_fits_1d.to_csv(f"qc/marginals/{model}_1d_fits.csv", index=False)
    marginal_fits_2d.to_csv(f"qc/marginals/{model}_2d_fits.csv", index=False)

    fig_1d = utils.get_column_plot(
        real_data=real_df,
        synthetic_data=synthetic_df,
        column_name=marginal_fits_1d["Column"][0],
        metadata=metadata,
    )

    fig_1d.write_image(f"qc/marginals/{model}_worst_1d_fit.png", width=1500, height=800)
    plotly.offline.plot(fig_1d, filename=f"qc/marginals/{model}_worst_1d_fit.html")

    fig_2d = utils.get_column_pair_plot(
        real_data=real_df,
        synthetic_data=synthetic_df,
        column_names=[
            marginal_fits_2d["Column 1"][0],
            marginal_fits_2d["Column 2"][0],
        ],
        metadata=metadata,
    )
    plotly.offline.plot(fig_2d, filename=f"qc/marginals/{model}_worst_2d_fit.html")

    fig_2d.write_image(f"qc/marginals/{model}_worst_2d_fit.png", width=1500, height=800)


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