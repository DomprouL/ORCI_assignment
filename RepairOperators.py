import copy


def update_solution_metrics(solution):

    solution.total_profit = sum(r.profit for r in solution.routes)
    solution.total_time = sum(r.time for r in solution.routes)
    solution.total_load = sum(r.load for r in solution.routes)

def feasible_insertion(model, route, node, delta):

    if route.load + model.nodes[node].demand > model.capacity:
        return False

    if route.time + delta > model.t_max:
        return False

    return True

def greedy_repair(model, partial_solution, removed_nodes):

    sol = copy.deepcopy(partial_solution)

    for node in removed_nodes:

        best_route = None
        best_pos = None
        best_delta = float("inf")

        for route in sol.routes:

            for pos in range(1, len(route.nodes)):

                a = route.nodes[pos - 1]
                b = route.nodes[pos]

                delta = (
                    model.cost_matrix[a][node]
                    + model.cost_matrix[node][b]
                    - model.cost_matrix[a][b]
                )

                if not feasible_insertion(
                    model,
                    route,
                    node,
                    delta
                ):
                    continue

                if delta < best_delta:

                    best_delta = delta
                    best_route = route
                    best_pos = pos

        if best_route is not None:

            best_route.nodes.insert(best_pos, node)

            best_route.load += model.nodes[node].demand
            best_route.time += best_delta
            best_route.profit += model.nodes[node].profit

    update_solution_metrics(sol)

    return sol


import random


def random_repair(model, partial_solution, removed_nodes):

    sol = copy.deepcopy(partial_solution)

    random.shuffle(removed_nodes)

    for node in removed_nodes:

        inserted = False

        routes = sol.routes[:]
        random.shuffle(routes)

        for route in routes:

            positions = list(range(1, len(route.nodes)))
            random.shuffle(positions)

            for pos in positions:

                a = route.nodes[pos - 1]
                b = route.nodes[pos]

                delta = (
                    model.cost_matrix[a][node]
                    + model.cost_matrix[node][b]
                    - model.cost_matrix[a][b]
                )

                if feasible_insertion(model, route, node, delta):

                    route.nodes.insert(pos, node)

                    route.load += model.nodes[node].demand
                    route.time += delta
                    route.profit += model.nodes[node].profit

                    inserted = True
                    break

            if inserted:
                break

    update_solution_metrics(sol)

    return sol



def minimum_repair(model, partial_solution, removed_nodes):

    sol = copy.deepcopy(partial_solution)
    #sort first if they are mandatory or not
    removed_nodes.sort(key=lambda x: model.nodes[x].isMandatory, reverse=True)
    for node in removed_nodes:
        
        best_route = None
        best_pos = None
        best_delta = float("inf")

        for route in sol.routes:

            for pos in range(1, len(route.nodes)):

                a = route.nodes[pos - 1]
                b = route.nodes[pos]

                delta = (
                    model.cost_matrix[a][node]
                    + model.cost_matrix[node][b]
                    - model.cost_matrix[a][b]
                )

                if not feasible_insertion(
                    model,
                    route,
                    node,
                    delta
                ):
                    continue

                if delta < best_delta:

                    best_delta = delta
                    best_route = route
                    best_pos = pos

        if best_route is not None:

            best_route.nodes.insert(best_pos, node)

            best_route.load += model.nodes[node].demand
            best_route.time += best_delta
            best_route.profit += model.nodes[node].profit

    update_solution_metrics(sol)

    return sol
        
    
