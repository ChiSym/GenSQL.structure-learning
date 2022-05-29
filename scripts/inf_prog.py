def find_start_index(df):
    """Heuristic to find a starting point for analysis."""
    columns = df.columns.tolist()
    val_observed = set()
    for row_start_index, row in df.iterrows():
        val_observed.update(row[~row.isnull()].index.tolist())
        if len(val_observed) == len(columns):
            break
    return columns, row_start_index + 1


def init_stream(df):
    """Initialize stream, determines which rows and columns we start with."""
    # We start with all columns. This can be changed and columns can be
    # integrated later.
    # Every column we integrate needs to have at least one value. Users can
    # manually specify that. But to get users started, we simply scan how many
    # rows we need to ensure that the case for all columns.
    columns, row_start_index = find_start_index(df)
    return columns, row_start_index


def inf_prog(model):
    """Incorporate data and run rejuvenation inference."""
    # Loop over rows and insert them.
    model.save_checkpoint()
    for t in range(model.incorporated_rows, model.T):
        model.insert_rows([t])
        # Every 100 rows, transition the columns
        if (t % 100) == 0:
            model.transition_cols()
        # Every 50 rows, save a checkpoint.
        if (t % 50) == 0:
            model.save_checkpoint()
    model.transition(N=10)
    model.save_checkpoint()
    # Change the above to run more inference if you are not happy with inference
    # quality!
    return model
