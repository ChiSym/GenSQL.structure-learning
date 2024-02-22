#!/usr/bin/python3

import numpy as np
import pandas as pd

df = pd.read_csv("data/predictions.csv", header=0)

# Show some generic metrics for the results found in 'predictions.csv' in the
# current directory

X = df["true_value"]
Y = df["prediction"]

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

print("Accuracy...: %f" % accuracy_score(Y, X))
print("Precision..: %f" % precision_score(Y, X, average="macro"))
print("Recall.....: %f" % recall_score(Y, X, average="macro"))
print("F1.........: %f" % f1_score(Y, X, average="macro"))

# Also save to disk. Helpful to track the result with DVC.
result = pd.DataFrame(
    {
        "metric": ["Accuracy", "Precision", "Recall", "F1"],
        "score:": [
            accuracy_score(Y, X),
            precision_score(Y, X, average="macro"),
            recall_score(Y, X, average="macro"),
            f1_score(Y, X, average="macro"),
        ],
    }
)
result.to_csv("data/ml-metrics.csv", index=False)
