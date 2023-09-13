import pandas as pd
import argparse
import pickle
from sdv.single_table import CTGANSynthesizer, CopulaGANSynthesizer, GaussianCopulaSynthesizer, TVAESynthesizer
from sdv.metadata import SingleTableMetadata

def train_baseline():
    description = "train baseline models"
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--model", type=str, default="ctgan", help="model to train"
    )

    df = pd.read_csv("data/subsampled.csv")

    args = parser.parse_args()
    model = args.model

    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(data=df)

    if model == "ctgan":
        synthesizer = CTGANSynthesizer(metadata)

    elif model == "copula":
        synthesizer = CopulaGANSynthesizer(metadata)

    elif model == "tvae":
        synthesizer = TVAESynthesizer(metadata)

    synthesizer.fit(df)

    pickle.dump(synthesizer, open(f"data/{model}.pkl", "wb"))

    synthetic_data = synthesizer.sample(num_rows=len(df))
    synthetic_data.to_csv(f"data/synthetic-data-{model}.csv", index=False)

if __name__ == "__main__":
    train_baseline()