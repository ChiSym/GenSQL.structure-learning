from statsmodels.imputation.mice import MICE, MICEData
from statsmodels.regression.linear_model import OLS
import miceforest as mf
import click
import polars as pl


@click.command()
@click.option('--data', help='Path to the data file')
@click.option('--output', help='Path to the output data file')
def impute(data, output):
    df = pl.read_parquet(data)
    categorical_cols = [col for col in df.columns if df[col].dtype == pl.Utf8]
    pandas_df = df.to_pandas(categories=categorical_cols)
    new_col_names = [str(i) for i in range(len(pandas_df.columns))]
    pandas_df.columns = new_col_names

    kds = mf.ImputationKernel(
        pandas_df,
        save_all_iterations=True,
        random_state=1991
    )
    # Run the MICE algorithm for 2 iterations
    kds.mice(2)

    # Return the completed dataset.
    complete_df = kds.complete_data()
    complete_df.columns = df.columns
    polars_complete_df = pl.DataFrame(complete_df)
    polars_complete_df.write_parquet(output)
    polars_complete_df.write_csv(output.replace(".parquet", ".csv"))