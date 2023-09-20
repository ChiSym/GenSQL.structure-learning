import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from matplotlib import animation


def normal_hypers_plot(hypers_list):
    x = range(len(hypers_list))
    mu = [hypers["m"] for hypers in hypers_list]
    std = [hypers["s"] for hypers in hypers_list]

    return [[x, mu], [x, std]]


# def normal_hypers_plot(hypers, x_lim=-5, y_lim=5, n=100):
#     mu_m = hypers["m"]
#     mu_std = (hypers["s"] / hypers["r"]) ** .5
#     x_mu = np.linspace(mu_m - 2 * mu_std, mu_m + 2 * mu_std, n)
#     y_mu = stats.t.pdf(x_mu, hypers["nu"], loc=mu_m, scale=mu_std)

#     alpha_std  = hypers["nu"] / 2
#     beta_std = hypers["nu"] * hypers["s"] / 2

#     mode_std = alpha_std / (beta_std + 1)

#     x_std = np.geomspace(mode_std / 100, mode_std * 100, n)
#     y_std = stats.invgamma.pdf(x_std, hypers["nu"]/2, scale=2/hypers["s"])

#     return [[x_mu, y_mu], [x_std, y_std]]


def plot_structure(wrapper):
    n_iters = len(wrapper.diagnostics["logscore"])
    diagnostics = wrapper.diagnostics

    def get_matrix(i, view, dim_idxs):
        zr = diagnostics["view_clusters"][i][view]
        return np.repeat(zr[:, np.newaxis], len(dim_idxs), axis=1)

    def get_matrices(i):
        zv = diagnostics["column_partition"][i]
        return [get_matrix(i, view, dim_idxs) for view, dim_idxs in zv.items()]

    # one for structure, one for logscore, then plots for each hyper
    total_n_plots = 2 + n_col_hypers_plots(wrapper)

    fig = plt.figure(figsize=(14, 20))
    fig, axes = plt.subplots(1, (total_n_plots + 1) // 2)
    axes = axes.flatten()

    a = get_matrices(0)[0]
    im1 = axes[0].imshow(a, interpolation="none", aspect="auto", vmin=0, vmax=1)
    axes[0].set_title("structure")

    logscore = diagnostics["logscore"][0]
    text = axes[1].text(
        0.5,
        0.5,
        f"{logscore:.2f}",
        horizontalalignment="center",
        verticalalignment="center",
        transform=axes[1].transAxes,
    )
    axes[1].axis("off")
    axes[1].set_title("logscore")

    data = normal_hypers_plot([diagnostics["column_hypers"][0][0]])
    (mu_hypers,) = axes[2].plot(data[0][0], data[0][1])
    axes[2].set_title("mu posterior")
    (std_hypers,) = axes[3].plot(data[1][0], data[1][1])
    axes[3].set_title("std posterior")

    def animate_func(i):
        matrices = get_matrices(i)
        matrix = matrices[0]  # dpmm for now
        im1.set_array(matrix)
        logscore = diagnostics["logscore"][i]
        text.set_text(f"{logscore:.2f}")

        data = normal_hypers_plot(
            [hypers[0] for hypers in diagnostics["column_hypers"][: i + 1]]
        )

        mu_hypers.set_data(data[0])
        axes[2].relim()
        axes[2].autoscale_view()

        std_hypers.set_data(data[1])
        axes[3].relim()
        axes[3].autoscale_view()

        return [im1, text, mu_hypers, std_hypers]

    nSeconds = 10
    fps = 5

    anim = animation.FuncAnimation(
        fig,
        animate_func,
        frames=nSeconds * fps,
        interval=1000 / fps,  # in ms
    )
    anim.save("test_anim_cgpm.gif", writer="imagemagick", fps=fps)
    import ipdb

    ipdb.set_trace()


def n_col_hypers_plots(wrapper):
    return sum([n_col_hypers_plot(dim.cctype) for dim in wrapper.cgpm.dims()])


def n_col_hypers_plot(cctype):
    match cctype:
        case "bernoulli":
            return 2
        case "normal":
            return 2
        case "categorical":
            return 1
        case _:
            raise NotImplementedError


if __name__ == "__main__":
    plot_structure(wrapper)
