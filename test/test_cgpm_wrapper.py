from inferenceql_auto_modeling.cgpm import CGPMModel
import edn_format
import tempfile
import pandas as pd
import numpy as np


def test_metadata_preserves_independences_crosscat():
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

    cgpm = CGPMModel.from_data(
        df, schema, mapping_table, model=model, cgpm_params=cgpm_params
    )

    with tempfile.NamedTemporaryFile() as tmp:
        cgpm.to_metadata(tmp.name)
        new_cgpm = CGPMModel.from_metadata(tmp.name)

        assert new_cgpm.model_type == model
        assert new_cgpm.columns_to_not_transition == cgpm.columns_to_not_transition


def test_metadata_preserves_independences_dpmm():
    df = pd.read_csv("test/satellites/numericalized.csv")
    schema = edn_format.loads(
        open("test/satellites/cgpm-schema.edn", "rb").read(), write_ply_tables=False
    )
    mapping_table = edn_format.loads(
        open("test/satellites/mapping-table.edn", "rb").read(), write_ply_tables=False
    )

    model = "DPMM"

    cgpm = CGPMModel.from_data(
        df,
        schema,
        mapping_table,
        model=model,
    )

    with tempfile.NamedTemporaryFile() as tmp:
        cgpm.to_metadata(tmp.name)
        new_cgpm = CGPMModel.from_metadata(tmp.name)

        assert new_cgpm.model_type == model
        Zv = new_cgpm.cgpm.Zv().values()
        assert all(v == 0 for v in Zv)


def test_metadata_preserves_independences_independent():
    df = pd.read_csv("test/satellites/numericalized.csv")
    schema = edn_format.loads(
        open("test/satellites/cgpm-schema.edn", "rb").read(), write_ply_tables=False
    )
    mapping_table = edn_format.loads(
        open("test/satellites/mapping-table.edn", "rb").read(), write_ply_tables=False
    )

    model = "Independent"

    cgpm = CGPMModel.from_data(
        df,
        schema,
        mapping_table,
        model=model,
    )

    with tempfile.NamedTemporaryFile() as tmp:
        cgpm.to_metadata(tmp.name)
        new_cgpm = CGPMModel.from_metadata(tmp.name)

        assert new_cgpm.model_type == model
        Zv = new_cgpm.cgpm.Zv().values()
        assert len(Zv) == len(set(Zv))
        for view in new_cgpm.cgpm.views.values():
            Zrv = view.Zr().values()
            assert all(v == 0 for v in Zrv)


def test_metadata_preserves_grids():
    df = pd.read_csv("test/satellites/numericalized.csv")
    schema = edn_format.loads(
        open("test/satellites/cgpm-schema.edn", "rb").read(), write_ply_tables=False
    )
    mapping_table = edn_format.loads(
        open("test/satellites/mapping-table.edn", "rb").read(), write_ply_tables=False
    )

    model = "Independent"

    cgpm = CGPMModel.from_data(
        df,
        schema,
        mapping_table,
        model=model,
    )
    n_cols = len(cgpm.cgpm.X)

    old_grid = cgpm.hyper_grids

    new_alpha_grid = np.zeros(5).tolist()
    new_view_alphas_grid = {i: np.zeros(10).tolist() for i in range(n_cols)}
    new_cols_grid = {i: {"alpha": np.zeros(30).tolist()} for i in range(n_cols)}

    new_grid = {
        "alpha": new_alpha_grid,
        "view_alphas": new_view_alphas_grid,
        "column_hypers": new_cols_grid,
    }

    cgpm.set_hyper_grids(new_grid)

    with tempfile.NamedTemporaryFile() as tmp:
        cgpm.to_metadata(tmp.name)
        new_cgpm = CGPMModel.from_metadata(tmp.name)

        new_cgpm.hyper_grids == new_grid

        state = new_cgpm.cgpm

        assert np.all(state.crp.hyper_grids["alpha"] == new_grid["alpha"])

        for view_idx, view in state.views.items():
            assert np.all(
                view.crp.hyper_grids["alpha"] == new_grid["view_alphas"][view_idx]
            )

        for col_idx, dim in enumerate(state.dims()):
            for param_name in dim.hypers.keys():
                assert np.all(
                    dim.hyper_grids[param_name]
                    == new_grid["column_hypers"][col_idx][param_name]
                )
