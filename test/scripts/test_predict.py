import numpy as np
import pandas as pd
import pytest
import sys

sys.path.insert(0, "scripts")

from predict import recode_categoricals
from predict import impute_missing_features
from predict import train_ml_model

SCHEMA = {"foo": "numerical", "bar": "numerical", "baz": "nominal"}


def test_impute_no_missing_features():
    df_training = pd.DataFrame({"foo": [1, 3], "bar": [100, 200], "baz": ["a", "a"]})
    df_test = pd.DataFrame({"foo": [-1, -3], "bar": [999, 999], "baz": ["b", "b"]})

    def assert_column_equal(df1, df2, col):
        """Assert two columns in a Pandas dataframe are equal."""
        assert df1[col].tolist() == df2[col].tolist()

    df_training_imputed, df_test_imputed = impute_missing_features(
        df_training, df_test, SCHEMA
    )
    assert_column_equal(df_training_imputed, df_training, "foo")
    assert_column_equal(df_training_imputed, df_training, "bar")
    assert_column_equal(df_training_imputed, df_training, "baz")
    assert_column_equal(df_test_imputed, df_test, "foo")
    assert_column_equal(df_test_imputed, df_test, "bar")
    assert_column_equal(df_test_imputed, df_test, "baz")


def test_impute_missing_features():
    df_training = pd.DataFrame(
        {
            "foo": [1, None, 3],
            "bar": [None, 100, 200],
            "baz": ["a", None, None],
        }
    )
    df_test = pd.DataFrame(
        {
            "foo": [-1, None, -3],
            "bar": [None, 999, 999],
            "baz": ["b", "b", None],
        }
    )
    df_training_imputed, df_test_imputed = impute_missing_features(
        df_training, df_test, SCHEMA
    )
    assert df_training_imputed["foo"].tolist() == [1, 2, 3]
    assert df_training_imputed["bar"].tolist() == [150, 100, 200]
    assert df_training_imputed["baz"].tolist() == ["a"] * 3
    assert df_test_imputed["foo"].tolist() == [-1, 2, -3]
    assert df_test_imputed["bar"].tolist() == [150, 999, 999]
    assert df_test_imputed["baz"].tolist() == ["b", "b", "a"]


N = 100
# Wrapping all ys in a dataframe so that pytest error messages are easier to
# read, when things raile
Y_COLUMNS = pd.DataFrame(
    {
        "gaussian": np.random.normal(0, 1, size=(N,)),
        "binary": np.random.randint(0, 2, size=(N,)),
        "categorical": np.random.choice(["a", "b", "c"], size=(N,)),
    }
)


@pytest.mark.parametrize(
    "y_name,target_type",
    [
        ("gaussian", "numerical"),
        ("binary", "nominal"),
        ("categorical", "nominal"),
    ],
)
@pytest.mark.parametrize("ml_model_name", ["Random_forest", "GLM"])
def test_train_ml_model(y_name, target_type, ml_model_name):
    X = np.random.normal(0, 1, size=(N, 10))
    y = Y_COLUMNS[y_name]
    model = train_ml_model(X, y, target_type, ml_model_name)
    if target_type == "numerical":
        assert model.predict(X).shape == y.shape
        assert isinstance(model.predict(X)[0], float)
    else:
        assert model.predict_proba(X).shape[0] == y.shape[0]
        assert isinstance(model.predict_proba(X)[0, 0], float)
        assert 0.0 < model.predict_proba(X)[0, 0] < 1.0


def test_recode_categoricals():
    df_training = pd.DataFrame(
        {
            "foo": [1, 2, 3],
            "bar": ["a", "b", "a"],
            "baz": ["x", "y", "x"],
        }
    )
    df_test = pd.DataFrame(
        {
            "foo": [-1, -2, -3],
            "bar": ["b", "b", "b"],
            "baz": ["x", "y", "x"],
        }
    )
    target = "baz"
    schema = {"foo": "numerical", "bar": "nominal", "baz": "nominal"}
    df_training_recoded, df_test_recoded, col_names = recode_categoricals(
        df_training, df_test, schema, target
    )
    expected_new_cols = ["c_0", "c_1"]
    assert set(col_names) == set(["foo"] + expected_new_cols)
    assert {0, 1} == set(df_training_recoded[expected_new_cols].values.flatten())
    assert {0, 1} == set(df_test_recoded[expected_new_cols].values.flatten())
    assert {0} == set(df_test_recoded[expected_new_cols[0]].unique())
    assert {1} == set(df_test_recoded[expected_new_cols[1]].unique())
