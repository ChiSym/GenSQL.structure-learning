from structurelearningapi.dependence_probability import dependence_probability
from structurelearningapi.io import deserialize
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
    df.write_csv(out_file)