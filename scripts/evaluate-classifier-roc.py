#!/usr/bin/python3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, auc
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression

# Generate generic ROC curve for the results found in 'predictions.csv' in the
# current directory

df = pd.read_csv("data/predictions.csv", header=0)
yv = df["prediction"]
yp = df["predictive-probability"]
tv = df["true_value"]

# Create a new binary column that is 1 IFF the classifier prediction matches
# the true value. This is what roc_curve() seems to want, but I'm not 100%
# sure.
yt = [1 if yv[i] == tv[i] else 0 for i in range(len(tv))]

# Compute ROC curve and ROC area
fpr, tpr, thresholds = roc_curve(yt, yp)
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
plt.show()
