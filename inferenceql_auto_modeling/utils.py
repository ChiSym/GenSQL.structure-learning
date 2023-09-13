import time


def n_categories(column, mapping_table):
    return len(mapping_table[column])


def distarg(column, mapping_table, schema):
    return (
        {"k": n_categories(column, mapping_table)}
        if schema[column] == "categorical"
        else None
    )


def _proportion_done(N, S, iters, start):
    if S is None:
        p_seconds = 0
    else:
        p_seconds = (time.time() - start) / S
    if N is None:
        p_iters = 0
    else:
        p_iters = float(iters) / N
    return max(p_iters, p_seconds)


def replace(array, pred, replacement):
    """Destructively replace all instances in a 2D array that satisfy a
    predicate with a replacement.
    """
    return [[(y if not pred(y) else replacement) for y in x] for x in array]
