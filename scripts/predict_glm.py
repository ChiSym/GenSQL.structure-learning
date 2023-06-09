import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import yaml

from sklearn.linear_model import LogisticRegression

with open("params.yaml", "r") as f:
    params = yaml.safe_load(f.read())

targets = params["targets"]
reweighting_columns = params["reweight_on"]
# Load eriginal raw data, which numericalized/ordinal but with better columns
# names.
df_test_raw = pd.read_csv("data/test-orig.csv")
df_LPM_training_raw = pd.read_csv("data/data-orig.csv")
# Impute training columns with mean.
for c in reweighting_columns:
    df_LPM_training_raw[c].fillna(df_LPM_training_raw[c].mean(), inplace=True)
    df_test_raw[c].fillna(df_test_raw[c].mean(), inplace=True)

results = {}
for target in targets:
    # Only keep training rows data where target is not null.
    df_LPM_training_raw = df_LPM_training_raw[~df_LPM_training_raw[target].isnull()]
    # Train classifier
    clf = LogisticRegression(random_state=42, max_iter=1000).fit(
        df_LPM_training_raw[reweighting_columns].values,
        df_LPM_training_raw[target].values
    )
    # Only keep target values that are not null
    results[target] = clf.predict_proba(df_test_raw[reweighting_columns].values)[:,0]
# Save results.
pd.DataFrame(results).to_csv("data/predictions-glm.csv", index=False)
