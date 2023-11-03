import matplotlib.pyplot as plt
from sklearn.metrics import RocCurveDisplay
import numpy as np


fig, ax = plt.subplots(figsize=(6, 6))

sppl_yhat = np.load("data/lpm_yhat_endocrine.npy")
expert_yhat = np.load("data/expert_yhat_endocrine.npy")
naive_yhat = np.load("data/naive_yhat_endocrine.npy")
one_hot_outcome = np.load("data/ground_truth_endocrine.npy")

RocCurveDisplay.from_predictions(
    one_hot_outcome.ravel(),
    sppl_yhat.ravel(),
    plot_chance_level=True,
    name="Large Population Model",
    color="blue",
    ax=ax,
)

RocCurveDisplay.from_predictions(
    one_hot_outcome.ravel(),
    expert_yhat.ravel(),
    ax=ax,
    color="orange",
    name="General Linear Model\n(features and interactions coded by experts)"
)

RocCurveDisplay.from_predictions(
    one_hot_outcome.ravel(),
    naive_yhat.ravel(),
    ax=ax,
    color="green",
    name="General Linear Model\n(features selected randomly)"
)

plt.title("Predicting type of hormone therapy\nfrom demographic and clinical features")
plt.legend(prop = { "size": 8 })
plt.xlabel("False positive rate")
plt.ylabel("True positive rate")
plt.savefig("data/roc_endocrine.png")