import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import yaml

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder

with open("params.yaml", "r") as f:
    params = yaml.safe_load(f.read())

targets = params["targets"]
reweighting_columns = params["reweight_on"]
# Load eriginal raw data, which numericalized/ordinal but with better columns
# names.
df_test_raw = pd.read_csv("data/test-orig.csv")
df_LPM_training_raw = pd.read_csv("data/data-orig.csv")


# Create dummy encoding for categorical columns
categoricals = [c for c in reweighting_columns if c!="age"]
enc = OneHotEncoder(handle_unknown='error')
enc.fit(df_LPM_training_raw[categoricals])
# Transform training and test data.
X_transformed = enc.transform(df_LPM_training_raw[categoricals]).toarray()
X_pred_transformed = enc.transform(df_test_raw[categoricals]).toarray()
# Add new cols to df
col_names = ["age"]
for i in range(X_transformed.shape[1]):
    col_name = f"c_{i}"
    df_LPM_training_raw[col_name] = X_transformed[:,i]
    df_test_raw[col_name] = X_pred_transformed[:,i]
    col_names.append(col_name)


results = {}
for target in targets:
    # Only keep training rows data where target is not null.
    df_LPM_training_raw = df_LPM_training_raw[~df_LPM_training_raw[target].isnull()]
    # Train classifier
    clf = LogisticRegression(random_state=42, max_iter=1000).fit(
        df_LPM_training_raw[col_names].values,
        df_LPM_training_raw[target].values
    )
    # Only keep target values that are not null
    results[target] = clf.predict_proba(df_test_raw[col_names].values)[:,0]
# Save results.
pd.DataFrame(results).to_csv("data/predictions-glm.csv", index=False)
