from inferenceql_auto_modeling.cgpm import CGPMModel
import edn_format
import tempfile
import pandas as pd


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
