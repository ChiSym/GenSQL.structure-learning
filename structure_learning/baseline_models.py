from sdv.single_table import CTGANSynthesizer, TVAESynthesizer
from sdv.metadata import SingleTableMetadata

import pickle
import click
import orjson
import polars as pl


model_to_class = {
    "ctgan": CTGANSynthesizer,
    "tvae": TVAESynthesizer,
}


@click.command()
@click.option('--data', help='Path to the data file')
@click.option('--column_models', help='Path to the column models file')
@click.option('--model', help='Name of the model to be evaluated')
@click.option('--n_samples', help='Number of synthetic data samples')
def train_sample_baseline(data, column_models, model, n_samples):
    with open(column_models, "rb") as f:
        column_models = orjson.loads(f.read())

    df = pl.read_csv(
        data,
        dtypes={
            cm["name"]: pl.Utf8 
                if cm["distribution"] == "categorical" 
                else pl.Float64
            for cm in column_models
        }
    ).to_pandas()

    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(df)

    model_class = model_to_class[model]
    synthesizer = model_class(metadata, verbose=True, epochs=100)

    synthesizer.fit(df)

    with open(f"data/{model}.pkl", "wb") as f:
        pickle.dump(synthesizer, f)

    synthetic_data = synthesizer.sample(num_rows=n_samples)
    synthetic_data_path = f"data/synthetic-data-{model}.csv"

    synthetic_data.to_csv(synthetic_data_path, index=False)