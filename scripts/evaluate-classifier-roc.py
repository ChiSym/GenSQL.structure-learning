#!/usr/bin/python3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, auc
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
import yaml

# Generate generic ROC curve for the results found in 'predictions.csv' in the
# current directory

df = pd.read_csv("data/predictions.csv", header=0)
yv = df["prediction"]
yp = df["predictive-probability"]
tv = df["true_value"]

with open("params.yaml", "r") as f:
    params = yaml.safe_load(f.read())
# Get held-out configuration for evaluation.
pos_label = params["synthetic_data_evaluation"]["positive_label"]

# Compute ROC curve and ROC area
fpr, tpr, thresholds = roc_curve(tv, yp, pos_label=pos_label)
roc_auc = auc(fpr, tpr)

# Plot ROC curve
plt.figure()
plt.plot(fpr, tpr, color="darkorange", lw=2, label="ROC curve (area = %0.2f)" % roc_auc)
plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("Receiver Operating Characteristic")
plt.legend(loc="lower right")
plt.savefig("roc.png")
