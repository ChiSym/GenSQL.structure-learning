import numpy as np
from xgboost import XGBClassifier
random_forest = XGBClassifier(max_depth=2, n_estimators=10, eval_metric="error", use_label_encoder=False)
n = 100
nc = 10
X = np.random.normal(0, 1, size=(n,nc))
y = np.random.randint(2, size=n)
random_forest.fit(X=X, y=y)
print("Predictions:")
print(random_forest.predict(X))
print("===== Success! =====")



