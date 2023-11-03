import click
import json
import os


@click.command()
@click.option("--loom_samples_dir")
@click.option("--out_dir", default="data/cgpm/best")
def get_best_model(loom_samples_dir: str, out_dir: str):
    n_samples = len(os.listdir(loom_samples_dir))
    log_filenames = [os.path.join(loom_samples_dir, f"sample.{sample}/infer_log.json")
        for sample in range(n_samples)]

    infer_logs = [
        json.load(open(log_filename, "r"))
        for log_filename in log_filenames
    ]

    scores = [
        infer_log['args']['scores']['score']
        for infer_log in infer_logs
    ]
    best_idx = scores.index(max(scores))
    best_filename = os.path.join(f"data/cgpm/hydrated/sample.{best_idx}.json")

    os.makedirs(os.path.dirname(out_dir), exist_ok=True)
    os.system(f"cp {best_filename} {out_dir}/sample.0.json")