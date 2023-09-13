from inferenceql_auto_modeling.cgpm import CGPMModel
import edn_format
import tempfile
import pandas as pd
import numpy as np


def test_slice_sampling_changes_parameters():
    df = pd.read_csv("test/satellites/numericalized.csv")
    schema = edn_format.loads(
        open("test/satellites/cgpm-schema.edn", "rb").read(), write_ply_tables=False
    )
    mapping_table = edn_format.loads(
        open("test/satellites/mapping-table.edn", "rb").read(), write_ply_tables=False
    )

    model = "CrossCat"
    cgpm_params = {
        "dependence": {
            "Type_of_Orbit": [
                "Purpose",
            ]
        },
    }

    wrapper = CGPMModel.from_data(
        df, schema, mapping_table, model=model, cgpm_params=cgpm_params
    )

    state = wrapper.cgpm
    prev_alpha = state.crp.hypers["alpha"]

    wrapper.inference(N=1, kernels=["alpha", "view_alphas", "column_hypers"])

    assert prev_alpha != state.crp.hypers["alpha"]
