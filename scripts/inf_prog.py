# `num_rows_col_insert` is the desired number of row insertions between randomly inserting a new
# column. It may not be fulfilled if there are not enough rows. When not fulfilled, all columns we
# will be incorporated from the first iteration on. This is to allow for a successful SPN
# merge stage, which can not happen when individual Crosscat models have different columns
# incorporated in their final iteration.

num_rows_col_insert = 5


def init_stream(df):
    (num_rows, num_columns) = df.shape
    # This is the number of rows needed to to perform column inserts
    # at the desired frequency (in terms of number of rows).
    rows_needed = num_columns * num_rows_col_insert

    if num_rows < rows_needed:
        # Start inference with all the columns.
        columns = df.columns.tolist()
    else:
        columns = df.columns.tolist()[0:2]

    rows = 1
    return columns, rows


def inf_prog(model):
    for t in range(model.incorporated_rows, model.T):
        if (t % num_rows_col_insert) == 1:
            if len(model.other_cols()) > 0:
                model.insert_cols([model.random_other_col()])
        model.insert_rows([t])
        if t in [5, 10, 15]:
            model.transition_rows()
        else:
            model.transition_rows([t, t - 1])
        if (t % 10) == 0:
            model.transition_cols()
    return model
