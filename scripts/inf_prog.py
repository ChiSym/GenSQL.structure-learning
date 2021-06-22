import numpy as np
import random
import copy


def init_stream(_):
    # XXX: Allow to supply a df arg here and seed here.
    columns = ["Perigee_km", "Apogee_km"]
    rows = 1
    return columns, rows


def inf_prog(model, seed):
    model.save_checkpoint()
    random.seed(seed)  # Does the scope here persist?
    np.random.seed(seed)

    for t in range(1, model.X.shape[0]):
        inf_new_row(model, t)
    return model


def inf_new_row(model, t):
    other_cols = [c for c in model.col_names if c not in model.incorporated_cols]
    if (t % 5) == 1:
        if len(other_cols) > 0:
            col = np.random.choice(other_cols)
            cid = len(model.incorporated_cols)
            weigth = model.safe_incorporate_col(col)
            if weigth is not None:
                model.state.transition_dims(cols=[cid])
                model.state.transition(
                    1,
                    kernels=["alpha", "view_alphas", "column_hypers"],
                    progress=False,
                    cols=[cid],
                )
                model.save_checkpoint()
    model.safe_incorporate_row(t)
    model.state.transition(
        1, kernels=["alpha", "view_alphas", "column_hypers"], progress=False
    )
    if t in [50, 100, 150]:
        model.state.transition_view_rows()
        model.save_checkpoint()
    elif t > 2:
        model.state.transition_view_rows(rows=[t, t - 1, t - 2])
        model.save_checkpoint()
    else:
        model.state.transition_view_rows(rows=[t, t - 1])
        model.save_checkpoint()
    colids = copy.deepcopy(model.state.outputs)
    if (t % 20) == 0:
        random.shuffle(colids)
        for colid in colids:
            model.state.transition_dims(cols=[colid]),
            model.save_checkpoint()
