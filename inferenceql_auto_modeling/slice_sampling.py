import numpy as np

from scipy.optimize import minimize_scalar, brentq


def get_lower_upper(hyper):
    match hyper:
        # notation abuse here, since both bernoulli and categorical use an alpha parameter
        case "alpha" | "beta" | "r" | "s" | "nu":
            return (1e-10, 1e10)
        case "m":
            return (-1e10, 1e10)
        case _:
            raise NotImplementedError(f"Hyperparameter name {hyper} not found")


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
        hypers = state.dim_for(col).hypers
        for name, val in hypers.items():
            new_col_hyper = slice_sampling(
                state.dim_for(col), name, val, *get_lower_upper(name)
            )
            set_hyper(state.dim_for(col), name, new_col_hyper)


def set_hyper(dim, hyper, value):
    dim.hypers[hyper] = value
    for k in dim.clusters:
        dim.clusters[k].set_hypers(dim.hypers)


def get_logp(dim, hyper, grid_value):
    set_hyper(dim, hyper, grid_value)
    logp_k = 0
    for k in dim.clusters:
        logp_k += dim.clusters[k].logpdf_score()
    return logp_k


def slice_sampling(dim, hyper, x0, lower, upper, tol=0.1):
    nlogp = get_logp(dim, hyper, x0)
    z = nlogp - np.random.exponential()

    opt_fn = lambda x: z - get_logp(dim, hyper, x)

    try:
        x_low = brentq(opt_fn, lower, x0)
    except ValueError:
        x_low = lower
    # res = minimize_scalar(
    #   opt_fn, bounds=(lower, x0), method="bounded", tol=tol)

    # this is hacky: scipy seems to return success even when the tolerance is not met
    # in cases where the bound is really large, we'd rather not default to it
    # if opt_fn(x_low) > tol and lower > 0:
    #     x_low = lower
    try:
        x_high = brentq(opt_fn, x0, upper)
    except ValueError:
        x_high = upper

    if x_low == lower and x_high == upper:
        raise ValueError("Slice sampling failed to find a valid interval")

    import ipdb

    ipdb.set_trace()

    return np.random.uniform(x_low, x_high)
