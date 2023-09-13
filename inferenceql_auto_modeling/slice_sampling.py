import numpy as np
import random
from scipy.optimize import least_squares, brentq


def get_lower_upper(name):
    match name:
        # notation abuse here, since both bernoulli and categorical use an alpha parameter
        case "alpha" | "beta" | "r" | "s" | "nu":
            return np.array([1e-10, 1e10])
        case "m":
            return np.array([-1e10, 1e10])
        case _:
            raise NotImplementedError(f"Hyperparameter name {name} not found")


def kernel_alpha(state):
    x0 = state.crp.hypers["alpha"]
    new_alpha = slice_sampling(state.crp, "alpha", x0, *get_lower_upper("alpha"))
    set_hyper(state.crp, "alpha", new_alpha)


def kernel_view_alphas(state):
    for idx, view in state.views.items():
        x0 = view.crp.hypers["alpha"]
        new_view_alpha = slice_sampling(
            view.crp, "alpha", x0, *get_lower_upper("alpha")
        )
        set_hyper(view.crp, "alpha", new_view_alpha)


def kernel_column_hypers(state):
    n_cols = len(state.X)
    for col in range(n_cols):
        dim = state.dim_for(col)

        opt_fn = lambda x: -get_set_logp_dim(dim, x)

        x0_dict = dim.hypers

        hyper_names = list(x0_dict.keys())
        bounds = np.array([get_lower_upper(hyper) for hyper in hyper_names])
        x0 = [x for x in x0_dict.values()]
        res = least_squares(opt_fn, x0, bounds=bounds.T)

        # set the MAP
        [set_hyper(dim, hyper, val) for hyper, val in zip(hyper_names, res.x)]

        # then do slice sampling
        random.shuffle(hyper_names)
        for name in hyper_names:
            val = dim.hypers[name]
            new_col_hyper = slice_sampling(
                state.dim_for(col), name, val, *get_lower_upper(name)
            )
            set_hyper(state.dim_for(col), name, new_col_hyper)


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


def slice_sampling(dim, hyper, x0, lower, upper, tol=0.1):
    nlogp = get_set_logp(dim, hyper, x0)
    z = nlogp - np.random.exponential()

    opt_fn = lambda x: z - get_set_logp(dim, hyper, x)

    try:
        x_low = brentq(opt_fn, lower, x0)
    except ValueError:
        x_low = lower

    try:
        x_high = brentq(opt_fn, x0, upper)
    except ValueError:
        x_high = upper

    if x_low == lower and x_high == upper:
        raise ValueError("Slice sampling failed to find a valid interval")

    return np.random.uniform(x_low, x_high)
