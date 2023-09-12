import numpy as np
from scipy.optimize import brentq, minimize_scalar, least_squares


def get_lower_upper(name):
    match name:
        # notation abuse here, since both bernoulli and categorical use an alpha parameter
        case "alpha" | "beta" | "r" | "s" | "nu":
            return np.array([1e-10, 1e10])
        case "m":
            return np.array([-1e10, 1e10])
        case _:
            raise NotImplementedError(f"Hyperparameter name {name} not found")


def make_grid(name, x_low, x_high, n=30):
    match name:
        # notation abuse here, since both bernoulli and categorical use an alpha parameter
        # we get away with it because both in both cases the grid is logspaced
        case "alpha" | "beta" | "r" | "s" | "nu":
            return np.geomspace(x_low, x_high, num=n)
        case "m":
            return np.linspace(x_low, x_high, num=n)
        case _:
            raise NotImplementedError(f"Hyperparameter name {name} not found")


def set_hyper(dim, hyper, value):
    dim.hypers[hyper] = value
    for k in dim.clusters:
        dim.clusters[k].set_hypers(dim.hypers)


def get_set_logp(dim, hyper, grid_value):
    set_hyper(dim, hyper, grid_value)
    return get_logp(dim)


def get_logp(dim):
    logp_k = 0
    for k in dim.clusters:
        logp_k += dim.clusters[k].logpdf_score()
    return logp_k


def get_grid_bounds(dim, hyper, x0, lower, upper, rel_tol=1e-3, tol=1e-5):
    map_fn = lambda x: -get_set_logp(dim, hyper, x)
    res = least_squares(map_fn, x0, bounds=(lower, upper))
    x_map = res.x[0]
    y_map = res.fun[0]

    # check if x_map is at a boundary
    lower_fn = map_fn(lower)
    upper_fn = map_fn(upper)

    if lower_fn - y_map < tol:
        x_map, y_map = lower, lower_fn
    elif upper_fn - y_map < tol:
        x_map, y_map = upper, upper_fn

    opt_fn = lambda x: -y_map + np.log(rel_tol) - get_set_logp(dim, hyper, x)

    try:
        x_low = brentq(opt_fn, lower, x_map) if x_map > lower else lower
    except ValueError:
        import ipdb

        ipdb.set_trace()
    try:
        x_high = brentq(opt_fn, x_map, upper) if x_map < upper else upper
    except ValueError:
        import ipdb

        ipdb.set_trace()

    return x_low, x_high


def refine_hyper_grid(dim, hyper, x0, n):
    lower, upper = get_lower_upper(hyper)
    x_low, x_high = get_grid_bounds(dim, hyper, x0, lower, upper)
    return make_grid(hyper, x_low, x_high, n=n)


def refine_crp_hyper_grids(state, n=30):
    x0 = state.crp.hypers["alpha"]

    return refine_hyper_grid(state.crp, "alpha", x0, n=n)


def refine_view_hyper_grids(state, n=30):
    new_grid = {}
    for idx, view in state.views.items():
        x0 = view.crp.hypers["alpha"]

        new_grid[idx] = refine_hyper_grid(view.crp, "alpha", x0, n=n)

    return new_grid


def logp_normalgamma(dim, mu, r, s, nu):
    hyper_dict = {"mu": mu, "r": r, "s": s, "nu": nu}
    [set_hyper(dim, hyper, x0) for hyper, x0 in hyper_dict.items()]

    return get_logp(dim)


def logp_beta(dim, alpha, beta):
    hyper_dict = {"alpha": alpha, "beta": beta}
    [set_hyper(dim, hyper, x0) for hyper, x0 in hyper_dict.items()]

    return get_logp(dim)


def logp_dirichlet(dim, alpha):
    set_hyper(dim, "alpha", alpha)

    return get_logp(dim)


def get_set_logp_dim(dim, hyper_list):
    match dim.cctype:
        case "normal":
            return logp_normalgamma(dim, *hyper_list)
        case "bernoulli":
            return logp_beta(dim, *hyper_list)
        case "categorical":
            return logp_dirichlet(dim, *hyper_list)
        case _:
            raise NotImplementedError(f"CC type {dim.cctype} not found")


def refine_dim_hyper_grids(state):
    new_grid = {}
    n_cols = len(state.X)
    for col in range(n_cols):
        dim = state.dim_for(col)

        opt_fn = lambda x: -get_set_logp_dim(dim, x)

        x0_dict = dim.hypers

        hyper_names = x0_dict.keys()
        bounds = np.array([get_lower_upper(hyper) for hyper in hyper_names])
        x0 = [x for x in x0_dict.values()]
        res = least_squares(opt_fn, x0, bounds=bounds.T)

        new_grid_col = {hyper: [val] for hyper, val in zip(hyper_names, res.x)}

        new_grid[col] = new_grid_col

    return new_grid


def refine_grid(state, n=30):
    new_grid = {}

    new_grid["alpha"] = refine_crp_hyper_grids(state, n=n)
    new_grid["view_alphas"] = refine_view_hyper_grids(state, n=n)
    new_grid["column_hypers"] = refine_dim_hyper_grids(state)

    return new_grid
