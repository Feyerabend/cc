"""
compare_optimisers.py

Runs SGD, momentum, RMSprop, and Adam on two test functions and plots
their convergence trajectories on the loss surface contours.

Test functions:
  1. Quadratic bowl:  f(x, y) = x^2 + 5 y^2
     Elongated along y, which causes SGD to oscillate across the valley.
     Adaptive methods should converge more smoothly.

  2. Rosenbrock (banana):  f(x, y) = (1 - x)^2 + 100(y - x^2)^2
     A classic non-convex function with a curved narrow valley and a
     global minimum at (1, 1).  Gradient descent famously struggles here.
"""

import numpy as np
import matplotlib.pyplot as plt
from optimisers import SGD, SGDMomentum, RMSprop, Adam


def quadratic(params):
    x, y = params["theta"]
    loss = x ** 2 + 5.0 * y ** 2
    grad = np.array([2.0 * x, 10.0 * y])
    return loss, {"theta": grad}


def rosenbrock(params):
    x, y = params["theta"]
    loss = (1 - x) ** 2 + 100.0 * (y - x ** 2) ** 2
    dx = -2.0 * (1 - x) - 400.0 * x * (y - x ** 2)
    dy = 200.0 * (y - x ** 2)
    return loss, {"theta": np.array([dx, dy])}


def run_optimiser(opt, objective, n_steps=300):
    losses = []
    trajectory = [opt.params["theta"].copy()]
    for _ in range(n_steps):
        loss, grads = objective(opt.params)
        losses.append(loss)
        opt.step(grads)
        trajectory.append(opt.params["theta"].copy())
    return losses, np.array(trajectory)


def make_grid(fn, xlim, ylim, resolution=200):
    xs = np.linspace(*xlim, resolution)
    ys = np.linspace(*ylim, resolution)
    X, Y = np.meshgrid(xs, ys)
    Z = np.vectorize(lambda x, y: fn({"theta": np.array([x, y])})[0])(X, Y)
    return X, Y, Z


def plot_comparison(objective, name, start, xlim, ylim, n_steps, lr_map):
    colours = {
        "SGD": "tab:blue",
        "Momentum": "tab:orange",
        "RMSprop": "tab:green",
        "Adam": "tab:red",
    }

    X, Y, Z = make_grid(objective, xlim, ylim)

    fig, (ax_contour, ax_loss) = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(f"Optimiser comparison on {name}", fontsize=13)

    ax_contour.contourf(X, Y, np.log1p(Z), levels=40, cmap="Blues")
    ax_contour.contour(X, Y, np.log1p(Z), levels=40, colors="white",
                       linewidths=0.3, alpha=0.4)
    ax_contour.set_xlabel("x")
    ax_contour.set_ylabel("y")
    ax_contour.set_title("Trajectories (log-scaled contours)")

    for label, Opt, kwargs in [
        ("SGD",      SGD,         {"lr": lr_map["SGD"]}),
        ("Momentum", SGDMomentum, {"lr": lr_map["Momentum"], "momentum": 0.9}),
        ("RMSprop",  RMSprop,     {"lr": lr_map["RMSprop"]}),
        ("Adam",     Adam,        {"lr": lr_map["Adam"]}),
    ]:
        init_params = {"theta": start.copy()}
        opt = Opt(init_params, **kwargs)
        losses, traj = run_optimiser(opt, objective, n_steps=n_steps)

        ax_contour.plot(traj[:, 0], traj[:, 1], "-o", markersize=2,
                        linewidth=1.2, color=colours[label], label=label, alpha=0.85)
        ax_loss.plot(losses, linewidth=1.4, color=colours[label], label=label)

    ax_contour.legend()
    ax_loss.set_xlabel("Step")
    ax_loss.set_ylabel("Loss (log scale)")
    ax_loss.set_yscale("log")
    ax_loss.set_title("Loss convergence")
    ax_loss.legend()
    ax_loss.grid(True, linewidth=0.4, alpha=0.5)

    plt.tight_layout()
    fname = f"compare_{name.lower().replace(' ', '_')}.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    print(f"Saved {fname}")
    plt.show()


if __name__ == "__main__":
    plot_comparison(
        objective=quadratic,
        name="Quadratic Bowl",
        start=np.array([-1.8, 1.8]),
        xlim=(-2.5, 2.5),
        ylim=(-2.5, 2.5),
        n_steps=200,
        lr_map={"SGD": 0.05, "Momentum": 0.05, "RMSprop": 0.05, "Adam": 0.1},
    )

    plot_comparison(
        objective=rosenbrock,
        name="Rosenbrock",
        start=np.array([-1.2, 1.0]),
        xlim=(-2.0, 2.0),
        ylim=(-0.5, 3.0),
        n_steps=2000,
        lr_map={"SGD": 0.001, "Momentum": 0.001, "RMSprop": 0.005, "Adam": 0.01},
    )
