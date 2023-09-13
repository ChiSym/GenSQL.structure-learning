import pandas as pd
import argparse
from sdv.metadata import SingleTableMetadata
from sdmetrics.reports.single_table import QualityReport
from sdmetrics.reports import utils


def make_marginal_fit_metrics():
    description = "assess 1 and 2d marginal fits"
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--model", type=str, default="lpm", help="model for which to assess fit"
    )
    parser.add_argument(
        "--real_data", type=str, default="data/ignored.csv", help="real data path"
    )

    args = parser.parse_args()
    model = args.model
    synthetic_data_path = f"data/synthetic-data-{model}.csv"

    real_data = pd.read_csv(args.real_data)
    synthetic_data = pd.read_csv(synthetic_data_path)

    # should we be using mapping table instead?
    metadata_obj = SingleTableMetadata()
    metadata_obj.detect_from_dataframe(data=real_data)
    metadata = metadata_obj.to_dict()

    report = QualityReport()
    report.generate(real_data, synthetic_data, metadata)

    marginal_fits_1d = report.get_details(property_name="Column Shapes").sort_values(
        "Score"
    )
    marginal_fits_2d = report.get_details(
        property_name="Column Pair Trends"
    ).sort_values("Score")

    marginal_fits_1d.to_csv(f"qc/marginals/{model}_1d_fits.csv", index=False)
    marginal_fits_2d.to_csv(f"qc/marginals/{model}_2d_fits.csv", index=False)

    fig_1d = utils.get_column_plot(
        real_data=real_data,
        synthetic_data=synthetic_data,
        column_name=marginal_fits_1d["Column"][0],
        metadata=metadata,
    )

    fig_1d.write_image(f"qc/marginals/{model}_worst_1d_fit.png")

    fig_2d = utils.get_column_pair_plot(
        real_data=real_data,
        synthetic_data=synthetic_data,
        column_names=[
            marginal_fits_2d["Column 1"][0],
            marginal_fits_2d["Column 2"][0],
        ],
        metadata=metadata,
    )

    fig_2d.write_image(f"qc/marginals/{model}_worst_2d_fit.png")


if __name__ == "__main__":
    make_marginal_fit_metrics()
