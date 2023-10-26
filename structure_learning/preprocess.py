import click
import orjson
import polars as pl
from structurelearningapi.column_model import create_column_model

@click.command()
@click.option('--data', help='Path to the data file')
@click.option('--sql', default="SELECT * FROM data", help='SQL query for preprocessing')
@click.option('--output', help='Path to the output file')
@click.option('--column_model_output', help='Path to the column models output file')
def preprocess(data, sql, output, column_model_output):
    data = pl.read_csv(data, infer_schema_length=None)
    data = data.sample(fraction=1, shuffle=True, seed=123)
    preprocessed = pl.SQLContext(data=data).execute(
        sql
    )
    preprocessed = preprocessed.collect()

    preprocessed  = preprocessed.with_columns(
        pl.col(pl.Utf8).str.replace_all("[^\p{Ascii}]", "")
    )

    model = create_column_model(preprocessed)

    with open(column_model_output, 'wb') as f:
        f.write(orjson.dumps(model, option=orjson.OPT_INDENT_2))

    preprocessed.write_csv(output)

@click.command()
@click.option('--column_models', help='Path to the column models file.')
@click.option('--output', help='Path to the output file.')
def loom_schema(column_models, output):
    with open(column_models, 'rb') as f:
        column_models = orjson.loads(f.read())
    schema = {
        cm["name"]: loom_type(cm["distribution"])
        for cm in column_models
    }

    with open(output, 'wb') as f:
        f.write(orjson.dumps(schema, option=orjson.OPT_INDENT_2))

def loom_type(distribution):
    match distribution:
        case "categorical":
            return "dd"
        case "normal":
            return "nich" 
        case _:
            raise NotImplementedError(f"Unsupported distribution: {distribution}")