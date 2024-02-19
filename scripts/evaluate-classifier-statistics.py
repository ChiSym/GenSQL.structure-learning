#!/usr/bin/python3

import numpy as np
import pandas as pd
df = pd.read_csv("predictions.csv",header=0)

# Show some generic metrics for the results found in 'predictions.csv' in the
# current directory

X=df['true_value']
Y=df['prediction']

from sklearn.metrics import accuracy_score,f1_score,precision_score,recall_score
print("Accuracy...: %f" % accuracy_score(Y,X))
print("Precision..: %f" % precision_score(Y,X,average='macro'))
print("Recall.....: %f" % recall_score(Y,X,average='macro'))
print("F1.........: %f" % f1_score(Y,X,average='macro'))
