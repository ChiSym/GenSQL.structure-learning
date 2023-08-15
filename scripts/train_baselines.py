import pandas as pd
import argparse
import pickle
from sdv.single_table import (
    CTGANSynthesizer,
    CopulaGANSynthesizer,
    GaussianCopulaSynthesizer,
    TVAESynthesizer,
)
from sdv.metadata import SingleTableMetadata


def train_baseline():
    description = "train baseline models"
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("--model", type=str, default="ctgan", help="model to train")
    parser.add_argument(
        "--data", type=str, default="data/nullified.csv", help="input data"
    )

    args = parser.parse_args()
    model = args.model
    df = pd.read_csv(args.data)

    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(data=df)

    match model:
        case "ctgan":
            synthesizer = CTGANSynthesizer(metadata)
        case "copula":
            synthesizer = CopulaGANSynthesizer(metadata)
        case "tvae":
            synthesizer = TVAESynthesizer(metadata)
        case _:
            raise NotImplementedError(f"model {model} not implemented")

    synthesizer.fit(df)

    pickle.dump(synthesizer, open(f"data/{model}.pkl", "wb"))

    synthetic_data = synthesizer.sample(num_rows=len(df))
    synthetic_data.to_csv(f"data/synthetic-data-{model}.csv", index=False)


if __name__ == "__main__":
    train_baseline()
