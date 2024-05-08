from structurelearningapi.dependence_probability import dependence_probability, reorder
from structurelearningapi.io import deserialize
import json
import click
import os

@click.command()
@click.option("--model_dir")
@click.option("--out_file")
def save_dependence_probability(model_dir, out_file):
    model_filenames = os.listdir(model_dir)
    models = [
        deserialize(os.path.join(model_dir, sample_filename))
        for sample_filename in model_filenames]

    df = dependence_probability(models)
    sorted_cols = reorder(df)
    import ipdb; ipdb.set_trace()

    with open("resources/dependence_probability_template.json", "r") as f:
        template = f.read()

    template = template.replace('<sorted_cols>', json.dumps(sorted_cols))
    with open("resources/dependence_probability.json", "w") as f:
        f.write(template)

    df.write_csv(out_file)