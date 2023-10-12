import click
import pandas as pd
from structurelearningapi.create_model import create_model
from structurelearningapi.io import serialize


@click.command()
@click.option('--data', help='Path to the data file')
@click.option('--output', help='Path to the data file')
def create_model(data):
    df = pd.read_csv(data)
    model = create_model(df)

    print(serialize(model).decode())

if __name__ == "__main__":
    create_model()