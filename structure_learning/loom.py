import orjson
import click

@click.command()
@click.option("--loom_filename")
@click.option("--column_model_filename", default="data/column_models.json")
def loom_to_cgpm(loom_filename, column_model_filename):
    with open(loom_filename, "rb") as f:
        model_metadata = orjson.loads(f.read())

    with open("loom/samples/sample.0/assign.json", "rb") as f:
        assign_metadata = orjson.loads(f.read())

    with open(column_model_filename, "rb") as f:
        column_model = orjson.loads(f.read())

    kinds = model_metadata["kinds"]

    for view in kinds:
        col_idxs = view["featureids"]
        col_names = [column_model[i]["name"] for i in col_idxs]

    import ipdb; ipdb.set_trace()