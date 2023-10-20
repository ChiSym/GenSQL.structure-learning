import numpy as np
import polars as pl
import click


@click.command()
def make_synthetic_categorical_data():
    cat = np.random.choice(
        ["a", "b"], size=1000, p=[0.9, 0.1]
    )
    df = pl.DataFrame({"cat": cat})
    df.write_csv("data/data.csv")