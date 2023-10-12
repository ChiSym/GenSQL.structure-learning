import click
import polars as pl
from structurelearningapi.create_model import create_model
from structurelearningapi.io import serialize
import numpy as np


@click.command()
@click.option('--data', help='Path to the data file')
@click.option('--seed', help='Seed number')
@click.option('--output', help='Path to the data file')
def create_model(data, seed, output):
    df = pl.read_csv(data)
    rng = np.random.RandomState(seed)
    model = create_model(df, rng)

    with open(output, 'wb') as f:
        f.write(serialize(model))

if __name__ == "__main__":
    create_model()