import click
import polars as pl
from lpm_discretize.discretize import discretize_quantiles

@click.command()
@click.option('--quantiles', type=click.INT, help='Number of quantiles to use when discretizing data')
@click.option('--model', help='Name of models whose synthetic data we should discretize', multiple=True)
def discretize(quantiles, model):
    data_dir = "data/"
    datafiles = [f"{data_dir}test.parquet"] + [f"data/synthetic-data-{m}.parquet" for m in model]

    dfs = [pl.read_parquet(datafile) for datafile in datafiles]


    discretized_dfs = discretize_quantiles(dfs, reference_idx = 0, quantiles=quantiles, columns=None, decimals=1)

    for df, datafile in zip(discretized_dfs, datafiles):
        datafile_strs = datafile.split("/")
        datafile_strs[-1] = f"discretized-{datafile_strs[-1]}"
        discretized_datafile = "/".join(datafile_strs)
        discretized_datafile_csv = discretized_datafile.replace(".parquet", ".csv")
        
        df.write_parquet(discretized_datafile)
        df.write_csv(discretized_datafile_csv)