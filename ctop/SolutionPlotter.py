"""Render routes in a shared two-dimensional distance embedding."""
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from sklearn.manifold import MDS


def infer_coordinates(model):
    matrix = np.array(model.cost_matrix)
    symmetric_distances = (matrix + matrix.T) / 2
    return MDS(
        n_components=2, metric="precomputed", metric_mds=True,
        init="random", n_init=1, random_state=42,
    ).fit_transform(symmetric_distances)


def plot_ctop_solution(model, routes, coords, title, enforce_mandatory, output_path):
    fig, ax = plt.subplots(figsize=(8, 6))
    assigned = {node for route in routes for node in route}
    unassigned = [node for node in range(1, model.num_nodes) if node not in assigned]
    ax.scatter(*coords[unassigned].T, color="#c8ced6", s=12, label="Unserved", zorder=1)

    for index, route in enumerate(routes):
        ax.plot(*coords[route].T, "o-", markersize=3.5, linewidth=1.15,
                label=f"Vehicle {index + 1}", zorder=2)

    if enforce_mandatory:
        required = [node.id for node in model.nodes if node.isMandatory and node.id != 0]
        ax.scatter(*coords[required].T, facecolors="none", edgecolors="#25303b",
                   s=35, linewidths=0.85, label="Required stop", zorder=3)

    ax.scatter(*coords[0], color="#222222", marker="s", s=50, label="Depot", zorder=4)
    ax.set(title=title, xlabel="MDS dimension 1", ylabel="MDS dimension 2", aspect="equal")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=4, frameon=False)
    ax.grid(alpha=0.15)
    fig.savefig(output_path, dpi=145, bbox_inches="tight")
    plt.close(fig)
