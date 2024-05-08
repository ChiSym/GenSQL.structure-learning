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
@click.option('--model', help='Name of the model to be evaluated')
def train_baseline(data, model):
    df = pl.read_parquet(data).to_pandas()
    for col in df.columns:
        if df[col].dtype == "category":
            df[col] = df[col].astype(str)

    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(df)

    model_class = model_to_class[model]
    synthesizer = model_class(metadata, epochs=100)

    synthesizer.fit(df)

    with open(f"data/{model}.pkl", "wb") as f:
        pickle.dump(synthesizer, f)