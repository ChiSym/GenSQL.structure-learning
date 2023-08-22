from inferenceql_auto_modeling.grid_refinement import refine_grid
from inferenceql_auto_modeling.cgpm import CGPMModel
import pandas as pd
import edn_format
import numpy as np


def test_refine_grid():
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

    cgpm_wrapper = CGPMModel.from_data(
        df, schema, mapping_table, model=model, cgpm_params=cgpm_params
    )
    n = 11
    state = cgpm_wrapper.cgpm

    new_grid = refine_grid(state, n=11)

    assert np.isclose(new_grid["alpha"][n // 2], state.crp.hypers["alpha"])

    for idx, view in state.views.items():
        assert np.isclose(
            new_grid["view_alphas"][idx][n // 2], view.crp.hypers["alpha"]
        )

    n_cols = len(state.X)
    for col in range(n_cols):
        final_hypers = state.dim_for(col).hypers
        for name, val in final_hypers.items():
            assert np.isclose(new_grid["column_hypers"][col][name][n // 2], val)
