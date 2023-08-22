import numpy as np


def refine_geomspace(final_hyper, grid, n=30):
    prev_n = len(grid)
    step = grid[1] / grid[0]
    width = step ** (prev_n // 2)

    new_grid = np.geomspace(final_hyper / width, final_hyper * width, n)
    return new_grid


def refine_linspace(final_hyper, grid, n=30):
    prev_n = len(grid)
    step = grid[1] - grid[0]
    width = step * (prev_n // 2)

    new_grid = np.geomspace(final_hyper - width, final_hyper + width, n)
    return new_grid


def refine_col(name, final_hyper, grid, n=30):
    match name:
        # notation abuse here, since both bernoulli and categorical use an alpha parameter
        # we get away with it because both in both cases the grid is logspaced
        case "alpha" | "beta" | "r" | "s" | "nu":
            return refine_geomspace(final_hyper, grid, n=n)
        case "m":
            return refine_linspace(final_hyper, grid, n=n)
        case _:
            raise NotImplementedError(f"Hyperparameter name {name} not found")


def refine_crp_hyper_grids(state, n=30):
    final_hyper = state.crp.hypers["alpha"]
    prev_grid = state.crp.hyper_grids["alpha"]

    new_grid = refine_geomspace(final_hyper, prev_grid, n=n)
    return new_grid


def refine_view_hyper_grids(state, n=30):
    new_grid = {}
    for idx, view in state.views.items():
        final_hyper = view.crp.hypers["alpha"]
        prev_grid = state.views[idx].crp.hyper_grids["alpha"]

        new_grid[idx] = refine_geomspace(final_hyper, prev_grid, n=n)

    return new_grid


def refine_dim_hyper_grids(state, n=30):
    new_grid = {}
    n_cols = len(state.X)
    for col in range(n_cols):
        new_grid_col = {}
        final_hypers = state.dim_for(col).hypers
        for name, val in final_hypers.items():
            prev_grid = state.dim_for(col).hyper_grids[name]
            new_grid_col[name] = refine_col(name, val, prev_grid, n=n)

        new_grid[col] = new_grid_col

    return new_grid


def refine_grid(state, n=30):
    new_grid = {}
    new_grid["alpha"] = refine_crp_hyper_grids(state, n=n)
    new_grid["view_alphas"] = refine_view_hyper_grids(state, n=n)
    new_grid["column_hypers"] = refine_dim_hyper_grids(state, n=n)

    return new_grid
