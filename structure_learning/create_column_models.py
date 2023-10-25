import click
import polars as pl
import orjson
from structurelearningapi.column_model import create_column_model


@click.command()
@click.option('--data', help='Path to the data file')
@click.option('--output', help='Path to the data file')
def create_column_models(data, output):
    df = pl.read_csv(data, infer_schema_length=None)
    model = create_column_model(df)

    with open(output, 'wb') as f:
        f.write(orjson.dumps(model, option=orjson.OPT_INDENT_2))