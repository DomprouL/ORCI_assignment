import random
import copy


def update_solution_metrics(solution):
    solution.total_profit = sum(r.profit for r in solution.routes)
    solution.total_time = sum(r.time for r in solution.routes)
    solution.total_load = sum(r.load for r in solution.routes)


def random_destroy(model, solution, remove_ratio=0.2):

    sol = copy.deepcopy(solution)

    all_nodes = []

    for r_idx, route in enumerate(sol.routes):

        for pos in range(1, len(route.nodes) - 1):

            node = route.nodes[pos]

            all_nodes.append((r_idx, pos, node))

    remove_count = max(1, int(len(all_nodes) * remove_ratio))

    selected = random.sample(all_nodes, remove_count)

    removed_nodes = []

    # reverse sorting to avoid index shifting
    selected.sort(reverse=True)

    for r_idx, pos, node in selected:

        route = sol.routes[r_idx]

        a = route.nodes[pos - 1]
        b = route.nodes[pos + 1]

        delta = (
            model.cost_matrix[a][node]
            + model.cost_matrix[node][b]
            - model.cost_matrix[a][b]
        )

        route.nodes.pop(pos)

        route.load -= model.nodes[node].demand
        route.time -= delta
        route.profit -= model.nodes[node].profit

        removed_nodes.append(node)

    update_solution_metrics(sol)

    return sol, removed_nodes




def worst_destroy(model, solution, remove_ratio=0.2):

    sol = copy.deepcopy(solution)

    candidates = []

    for r_idx, route in enumerate(sol.routes):

        for pos in range(1, len(route.nodes) - 1):

            node = route.nodes[pos]

            a = route.nodes[pos - 1]
            b = route.nodes[pos + 1]

            delta = (
                model.cost_matrix[a][node]
                + model.cost_matrix[node][b]
                - model.cost_matrix[a][b]
            )

            if delta <= 0:
                continue

            score = model.nodes[node].profit / delta

            candidates.append((score, r_idx, pos, node))

    candidates.sort()

    remove_count = max(1, int(len(candidates) * remove_ratio))

    selected = candidates[:remove_count]

    removed_nodes = []

    selected.sort(reverse=True, key=lambda x: x[2])

    for _, r_idx, pos, node in selected:

        route = sol.routes[r_idx]

        a = route.nodes[pos - 1]
        b = route.nodes[pos + 1]

        delta = (
            model.cost_matrix[a][node]
            + model.cost_matrix[node][b]
            - model.cost_matrix[a][b]
        )

        route.nodes.pop(pos)

        route.load -= model.nodes[node].demand
        route.time -= delta
        route.profit -= model.nodes[node].profit

        removed_nodes.append(node)

    update_solution_metrics(sol)

    return sol, removed_nodes