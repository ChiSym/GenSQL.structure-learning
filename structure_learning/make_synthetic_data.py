import numpy as np
import polars as pl

def make_cat(val):
    if val > 0.:
        return np.random.choice(["a", "b"], p=[.9, .1])
    else:
        return np.random.choice(["a", "b"], p=[.1, .9])

def make_synthetic_data():
    arr1 = np.random.normal([0, 1, 2], scale=[.1, .2, .3], size=(100, 3))
    arr2 = np.random.normal([0, -1, -2], scale=[.1, .2, .3], size=(100, 3))
    arr3 = np.random.normal([-5, 5, 3], scale=[.3, .2, .1], size=(100, 3))

    sum1 = np.random.normal(0, scale=1, size=100)
    sum2 = np.random.normal(0, scale=1, size=100)
    sum3 = np.random.normal(0, scale=1, size=100)

    cat1 = np.array([make_cat(s) for s in sum1])
    cat2 = np.array([make_cat(s) for s in sum2])
    cat3 = np.array([make_cat(s) for s in sum3])

    X = np.hstack((
        arr1 + sum1[:, np.newaxis],
        arr2 + sum2[:, np.newaxis],
        arr3 + sum3[:, np.newaxis],
        cat1[:, np.newaxis],
        cat2[:, np.newaxis],
        cat3[:, np.newaxis],

    ))

    df =  pl.DataFrame(X)
    df.write_csv("data/data.csv")

if __name__ == "__main__":
    make_synthetic_data()