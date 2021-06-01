#!/usr/bin/env bash

# Create the target directory.
mkdir data
# Move data there.
cp test/satellites/data.csv data/data.csv
cp test/satellites/params.yaml params.yaml
# Run the complete pipeline.
source .venv/bin/activate && python3.9 -m dvc repro -f
