import click
import duckdb
import orjson
import polars as pl

@click.command()
@click.option('--data', help='Path to the data file')
@click.option('--sql', default="SELECT * FROM data", help='SQL query for preprocessing')
@click.option('--output', help='Path to the output file')
def preprocess(data, sql, output):
    data = pl.read_csv(data)
    duckdb.sql(sql).write_csv(output)

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