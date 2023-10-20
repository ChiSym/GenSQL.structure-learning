import click
import polars as pl
import plotly
from sdv.metadata import SingleTableMetadata
from sdmetrics.reports.single_table import QualityReport
from sdmetrics.reports import utils

def get_sdv_type(col):
    if col.is_numeric():
        return "numerical"
    else:
        return "categorical"

@click.command()
@click.option('--real_data', help='Path to the real data file')
@click.option('--model', help='Name of the model to be evaluated')
def marginal_fits(real_data, model):
    synthetic_data_path = f"data/synthetic-data-{model}.csv"

    real_df = pl.read_csv(real_data).to_pandas()
    synthetic_df = pl.read_csv(synthetic_data_path).to_pandas()

    # should we be using mapping table instead?
    metadata_obj = SingleTableMetadata()
    metadata_obj.detect_from_dataframe(real_df)
    metadata = metadata_obj.to_dict()

    report = QualityReport()
    report.generate(real_df, synthetic_df, metadata)

    marginal_fits_1d = report.get_details(property_name="Column Shapes").sort_values(
        "Score"
    )
    marginal_fits_2d = report.get_details(
        property_name="Column Pair Trends"
    ).sort_values("Score")

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

    # fig_2d = utils.get_column_pair_plot(
    #     real_data=real_df,
    #     synthetic_data=synthetic_df,
    #     column_names=[
    #         marginal_fits_2d["Column 1"][0],
    #         marginal_fits_2d["Column 2"][0],
    #     ],
    #     metadata=metadata,
    # )
    # plotly.offline.plot(fig_2d, filename=f"qc/marginals/{model}_worst_2d_fit.html")

    # fig_2d.write_image(f"qc/marginals/{model}_worst_2d_fit.png", width=1500, height=800)
