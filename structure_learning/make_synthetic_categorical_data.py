import numpy as np
import polars as pl
import click


@click.command()
def make_synthetic_categorical_data():
    cat = np.random.choice(
        ["a", "b", "c"], size=100, p=[0.9, 0.09, 0.01]
    )
    df = pl.DataFrame({"cat": cat})
    df.write_csv("data/data.csv")