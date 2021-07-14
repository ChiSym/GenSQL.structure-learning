def init_stream(_):
    columns = ["Perigee_km", "Apogee_km"]
    rows = 1
    return columns, rows


def inf_prog(model):
    for t in range(model.incorporated_rows, model.T):
        if (t % 5) == 1:
            if len(model.other_cols()) > 0:
                model.insert_cols([model.random_other_col()])
        model.insert_rows([t])
        if t in [50, 100, 150]:
            model.transition_rows()
        else:
            model.transition_rows([t, t - 1])
        if (t % 20) == 0:
            model.transition_cols()
    return model
