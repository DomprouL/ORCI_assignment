EPSILON = 1e-6


# Computes the total travel time of a route based on the sequence of nodes.
def compute_route_time(model, nodes):
    total_time = 0.0

    for i in range(len(nodes) - 1):
        a = nodes[i]
        b = nodes[i + 1]
        total_time += model.cost_matrix[a][b]

    return total_time


# Computes the total load of a route based on the sequence of nodes.
def compute_route_load(model, nodes):
    total_load = 0

    for node_id in nodes:
        total_load += model.nodes[node_id].demand

    return total_load


# Computes the total profit of a route based on the sequence of nodes.
def compute_route_profit(model, nodes):
    total_profit = 0

    for node_id in nodes:
        total_profit += model.nodes[node_id].profit

    return total_profit


# Complete update of route values (time, load, profit) based on its current sequence of nodes.
def update_route_values(model, route):
    route.time = compute_route_time(model, route.nodes)
    route.load = compute_route_load(model, route.nodes)
    route.profit = compute_route_profit(model, route.nodes)


# Checks if a route starts and ends with the depot (node 0).
def is_route_structure_valid(route):
    if len(route.nodes) < 2:
        return False

    if route.nodes[0] != 0:
        return False

    if route.nodes[-1] != 0:
        return False

    return True


# Checks if a route is feasible with respect to depot structure, capacity and route time.
def is_route_feasible(model, route):
    if not is_route_structure_valid(route):
        return False

    if route.load > model.capacity:
        return False

    if route.time > model.t_max + EPSILON:
        return False

    return True


# Computes total travel time of all routes.
def total_solution_time(routes):
    total_time = 0.0

    for route in routes:
        total_time += route.time

    return total_time


# Computes total profit of all routes.
def total_solution_profit(routes):
    total_profit = 0

    for route in routes:
        total_profit += route.profit

    return total_profit


# Changes route's sequence of nodes to new_nodes. Then updates time, load and profit.
def apply_new_nodes_to_route(model, route, new_nodes):
    route.nodes = new_nodes
    update_route_values(model, route)


# Checks whether two nodes are considered close according to the nearest-neighbor/RCL structure.
def are_neighbors(a, b, neighbors_set_array):
    if a == 0 or b == 0:
        return True

    return (
        b in neighbors_set_array[a]
        or a in neighbors_set_array[b]
    )


# Intra 2-opt with RCL filtering.
def intra_2opt_best_improvement(model, route, neighbors_set_array):
    if len(route.nodes) <= 4:
        return False

    old_time = route.time
    best_time = old_time
    best_nodes = None

    nodes = route.nodes

    for i in range(1, len(nodes) - 2):
        for j in range(i + 1, len(nodes) - 1):

            a = nodes[i - 1]
            b = nodes[i]
            c = nodes[j]
            d = nodes[j + 1]

            if not (
                are_neighbors(a, c, neighbors_set_array)
                or are_neighbors(b, d, neighbors_set_array)
            ):
                continue

            new_nodes = (
                nodes[:i]
                + list(reversed(nodes[i:j + 1]))
                + nodes[j + 1:]
            )

            new_time = compute_route_time(model, new_nodes)

            if new_time < best_time - EPSILON:
                best_time = new_time
                best_nodes = new_nodes

    if best_nodes is None:
        return False

    apply_new_nodes_to_route(model, route, best_nodes)
    return True


# Intra relocate 1-0 with RCL filtering.
def intra_relocate_best_improvement(model, route, neighbors_set_array):
    if len(route.nodes) <= 3:
        return False

    old_time = route.time
    best_time = old_time
    best_nodes = None

    nodes = route.nodes

    for remove_pos in range(1, len(nodes) - 1):

        customer = nodes[remove_pos]
        remaining_nodes = nodes[:remove_pos] + nodes[remove_pos + 1:]

        for insert_pos in range(1, len(remaining_nodes)):

            if insert_pos == remove_pos or insert_pos == remove_pos + 1:
                continue

            left = remaining_nodes[insert_pos - 1]
            right = remaining_nodes[insert_pos]

            if not (
                are_neighbors(customer, left, neighbors_set_array)
                or are_neighbors(customer, right, neighbors_set_array)
            ):
                continue

            new_nodes = (
                remaining_nodes[:insert_pos]
                + [customer]
                + remaining_nodes[insert_pos:]
            )

            new_time = compute_route_time(model, new_nodes)

            if new_time < best_time - EPSILON:
                best_time = new_time
                best_nodes = new_nodes

    if best_nodes is None:
        return False

    apply_new_nodes_to_route(model, route, best_nodes)
    return True


# Intra swap 1-1 with RCL filtering.
def intra_swap_best_improvement(model, route, neighbors_set_array):
    if len(route.nodes) <= 3:
        return False

    old_time = route.time
    best_time = old_time
    best_nodes = None

    nodes = route.nodes

    for i in range(1, len(nodes) - 2):
        for j in range(i + 1, len(nodes) - 1):

            node_i = nodes[i]
            node_j = nodes[j]

            left_i = nodes[i - 1]
            right_i = nodes[i + 1]

            left_j = nodes[j - 1]
            right_j = nodes[j + 1]

            valid_for_i_position = (
                are_neighbors(node_j, left_i, neighbors_set_array)
                or are_neighbors(node_j, right_i, neighbors_set_array)
            )

            valid_for_j_position = (
                are_neighbors(node_i, left_j, neighbors_set_array)
                or are_neighbors(node_i, right_j, neighbors_set_array)
            )

            if not (valid_for_i_position and valid_for_j_position):
                continue

            new_nodes = nodes.copy()
            new_nodes[i], new_nodes[j] = new_nodes[j], new_nodes[i]

            new_time = compute_route_time(model, new_nodes)

            if new_time < best_time - EPSILON:
                best_time = new_time
                best_nodes = new_nodes

    if best_nodes is None:
        return False

    apply_new_nodes_to_route(model, route, best_nodes)
    return True


# Inter relocate 1-0 between two routes with RCL filtering.
def inter_relocate_best_improvement(model, route_a, route_b, neighbors_set_array):

    old_total_time = route_a.time + route_b.time
    best_total_time = old_total_time
    best_nodes_a = None
    best_nodes_b = None

    # Move one customer from route_a to route_b.
    for remove_pos in range(1, len(route_a.nodes) - 1):

        customer = route_a.nodes[remove_pos]
        new_nodes_a = route_a.nodes[:remove_pos] + route_a.nodes[remove_pos + 1:]

        for insert_pos in range(1, len(route_b.nodes)):

            left = route_b.nodes[insert_pos - 1]
            right = route_b.nodes[insert_pos]

            if not (
                are_neighbors(customer, left, neighbors_set_array)
                or are_neighbors(customer, right, neighbors_set_array)
            ):
                continue

            new_nodes_b = (
                route_b.nodes[:insert_pos]
                + [customer]
                + route_b.nodes[insert_pos:]
            )

            new_time_a = compute_route_time(model, new_nodes_a)
            new_time_b = compute_route_time(model, new_nodes_b)

            new_load_a = compute_route_load(model, new_nodes_a)
            new_load_b = compute_route_load(model, new_nodes_b)

            if new_load_a > model.capacity:
                continue

            if new_load_b > model.capacity:
                continue

            if new_time_a > model.t_max + EPSILON:
                continue

            if new_time_b > model.t_max + EPSILON:
                continue

            new_total_time = new_time_a + new_time_b

            if new_total_time < best_total_time - EPSILON:
                best_total_time = new_total_time
                best_nodes_a = new_nodes_a
                best_nodes_b = new_nodes_b

    # Move one customer from route_b to route_a.
    for remove_pos in range(1, len(route_b.nodes) - 1):

        customer = route_b.nodes[remove_pos]
        new_nodes_b = route_b.nodes[:remove_pos] + route_b.nodes[remove_pos + 1:]

        for insert_pos in range(1, len(route_a.nodes)):

            left = route_a.nodes[insert_pos - 1]
            right = route_a.nodes[insert_pos]

            if not (
                are_neighbors(customer, left, neighbors_set_array)
                or are_neighbors(customer, right, neighbors_set_array)
            ):
                continue

            new_nodes_a = (
                route_a.nodes[:insert_pos]
                + [customer]
                + route_a.nodes[insert_pos:]
            )

            new_time_a = compute_route_time(model, new_nodes_a)
            new_time_b = compute_route_time(model, new_nodes_b)

            new_load_a = compute_route_load(model, new_nodes_a)
            new_load_b = compute_route_load(model, new_nodes_b)

            if new_load_a > model.capacity:
                continue

            if new_load_b > model.capacity:
                continue

            if new_time_a > model.t_max + EPSILON:
                continue

            if new_time_b > model.t_max + EPSILON:
                continue

            new_total_time = new_time_a + new_time_b

            if new_total_time < best_total_time - EPSILON:
                best_total_time = new_total_time
                best_nodes_a = new_nodes_a
                best_nodes_b = new_nodes_b

    if best_nodes_a is None:
        return False

    apply_new_nodes_to_route(model, route_a, best_nodes_a)
    apply_new_nodes_to_route(model, route_b, best_nodes_b)

    return True


# Inter swap 1-1 between two routes with RCL filtering.
def inter_swap_best_improvement(model, route_a, route_b, neighbors_set_array):

    old_total_time = route_a.time + route_b.time
    best_total_time = old_total_time
    best_nodes_a = None
    best_nodes_b = None

    for pos_a in range(1, len(route_a.nodes) - 1):
        for pos_b in range(1, len(route_b.nodes) - 1):

            node_a = route_a.nodes[pos_a]
            node_b = route_b.nodes[pos_b]

            left_a = route_a.nodes[pos_a - 1]
            right_a = route_a.nodes[pos_a + 1]

            left_b = route_b.nodes[pos_b - 1]
            right_b = route_b.nodes[pos_b + 1]

            valid_for_a_position = (
                are_neighbors(node_b, left_a, neighbors_set_array)
                or are_neighbors(node_b, right_a, neighbors_set_array)
            )

            valid_for_b_position = (
                are_neighbors(node_a, left_b, neighbors_set_array)
                or are_neighbors(node_a, right_b, neighbors_set_array)
            )

            if not (valid_for_a_position and valid_for_b_position):
                continue

            new_nodes_a = route_a.nodes.copy()
            new_nodes_b = route_b.nodes.copy()

            new_nodes_a[pos_a], new_nodes_b[pos_b] = new_nodes_b[pos_b], new_nodes_a[pos_a]

            new_time_a = compute_route_time(model, new_nodes_a)
            new_time_b = compute_route_time(model, new_nodes_b)

            new_load_a = compute_route_load(model, new_nodes_a)
            new_load_b = compute_route_load(model, new_nodes_b)

            if new_load_a > model.capacity:
                continue

            if new_load_b > model.capacity:
                continue

            if new_time_a > model.t_max + EPSILON:
                continue

            if new_time_b > model.t_max + EPSILON:
                continue

            new_total_time = new_time_a + new_time_b

            if new_total_time < best_total_time - EPSILON:
                best_total_time = new_total_time
                best_nodes_a = new_nodes_a
                best_nodes_b = new_nodes_b

    if best_nodes_a is None:
        return False

    apply_new_nodes_to_route(model, route_a, best_nodes_a)
    apply_new_nodes_to_route(model, route_b, best_nodes_b)

    return True


# Inter 2-opt* between two routes with RCL filtering.
def inter_2opt_best_improvement(model, route_a, route_b, neighbors_set_array):

    old_total_time = route_a.time + route_b.time
    best_total_time = old_total_time
    best_nodes_a = None
    best_nodes_b = None

    nodes_a = route_a.nodes
    nodes_b = route_b.nodes

    for cut_a in range(1, len(nodes_a) - 1):
        for cut_b in range(1, len(nodes_b) - 1):

            prefix_a = nodes_a[:cut_a]
            suffix_a = nodes_a[cut_a:-1]

            prefix_b = nodes_b[:cut_b]
            suffix_b = nodes_b[cut_b:-1]

            if len(suffix_a) == 0 or len(suffix_b) == 0:
                continue

            last_prefix_a = prefix_a[-1]
            first_suffix_a = suffix_a[0]

            last_prefix_b = prefix_b[-1]
            first_suffix_b = suffix_b[0]

            if not (
                are_neighbors(last_prefix_a, first_suffix_b, neighbors_set_array)
                or are_neighbors(last_prefix_b, first_suffix_a, neighbors_set_array)
            ):
                continue

            new_nodes_a = prefix_a + suffix_b + [0]
            new_nodes_b = prefix_b + suffix_a + [0]

            new_time_a = compute_route_time(model, new_nodes_a)
            new_time_b = compute_route_time(model, new_nodes_b)

            new_load_a = compute_route_load(model, new_nodes_a)
            new_load_b = compute_route_load(model, new_nodes_b)

            if new_load_a > model.capacity:
                continue

            if new_load_b > model.capacity:
                continue

            if new_time_a > model.t_max + EPSILON:
                continue

            if new_time_b > model.t_max + EPSILON:
                continue

            new_total_time = new_time_a + new_time_b

            if new_total_time < best_total_time - EPSILON:
                best_total_time = new_total_time
                best_nodes_a = new_nodes_a
                best_nodes_b = new_nodes_b

    if best_nodes_a is None:
        return False

    apply_new_nodes_to_route(model, route_a, best_nodes_a)
    apply_new_nodes_to_route(model, route_b, best_nodes_b)

    return True


# Intra 2-opt local search.
def intra_2opt_local_search(model, route, neighbors_set_array):

    improved_at_least_once = False

    while True:
        improved = intra_2opt_best_improvement(model, route, neighbors_set_array)

        if not improved:
            break

        improved_at_least_once = True

    return improved_at_least_once


# Intra relocate local search.
def intra_relocate_local_search(model, route, neighbors_set_array):

    improved_at_least_once = False

    while True:
        improved = intra_relocate_best_improvement(model, route, neighbors_set_array)

        if not improved:
            break

        improved_at_least_once = True

    return improved_at_least_once


# Intra swap local search.
def intra_swap_local_search(model, route, neighbors_set_array):

    improved_at_least_once = False

    while True:
        improved = intra_swap_best_improvement(model, route, neighbors_set_array)

        if not improved:
            break

        improved_at_least_once = True

    return improved_at_least_once


# Inter 2-opt* local search.
def inter_2opt_local_search(model, routes, neighbors_set_array):

    improved_at_least_once = False

    while True:
        improved_in_iteration = False

        for i in range(len(routes) - 1):
            for j in range(i + 1, len(routes)):

                improved = inter_2opt_best_improvement(
                    model,
                    routes[i],
                    routes[j],
                    neighbors_set_array
                )

                if improved:
                    improved_at_least_once = True
                    improved_in_iteration = True

        if not improved_in_iteration:
            break

    return improved_at_least_once


# Inter relocate local search.
def inter_relocate_local_search(model, routes, neighbors_set_array):

    improved_at_least_once = False

    while True:
        improved_in_iteration = False

        for i in range(len(routes) - 1):
            for j in range(i + 1, len(routes)):

                improved = inter_relocate_best_improvement(
                    model,
                    routes[i],
                    routes[j],
                    neighbors_set_array
                )

                if improved:
                    improved_at_least_once = True
                    improved_in_iteration = True

        if not improved_in_iteration:
            break

    return improved_at_least_once


# Inter swap local search.
def inter_swap_local_search(model, routes, neighbors_set_array):

    improved_at_least_once = False

    while True:
        improved_in_iteration = False

        for i in range(len(routes) - 1):
            for j in range(i + 1, len(routes)):

                improved = inter_swap_best_improvement(
                    model,
                    routes[i],
                    routes[j],
                    neighbors_set_array
                )

                if improved:
                    improved_at_least_once = True
                    improved_in_iteration = True

        if not improved_in_iteration:
            break

    return improved_at_least_once


# Applies intra 2-opt to all routes.
def intra_2opt_all_routes_local_search(model, routes, neighbors_set_array):

    improved_at_least_once = False

    for route in routes:
        improved = intra_2opt_local_search(model, route, neighbors_set_array)

        if improved:
            improved_at_least_once = True

    return improved_at_least_once


# Applies intra relocate to all routes.
def intra_relocate_all_routes_local_search(model, routes, neighbors_set_array):

    improved_at_least_once = False

    for route in routes:
        improved = intra_relocate_local_search(model, route, neighbors_set_array)

        if improved:
            improved_at_least_once = True

    return improved_at_least_once


# Applies intra swap to all routes.
def intra_swap_all_routes_local_search(model, routes, neighbors_set_array):

    improved_at_least_once = False

    for route in routes:
        improved = intra_swap_local_search(model, route, neighbors_set_array)

        if improved:
            improved_at_least_once = True

    return improved_at_least_once


# VND that applies all RCL-restricted time operators in sequence.
def time_vnd(model, routes, neighbors_set_array):

    improved_at_least_once = False
    neighborhood_index = 0

    neighborhoods = [
        intra_2opt_all_routes_local_search,
        intra_relocate_all_routes_local_search,
        intra_swap_all_routes_local_search,
        inter_2opt_local_search,
        inter_relocate_local_search,
        inter_swap_local_search
    ]

    while neighborhood_index < len(neighborhoods):

        old_time = total_solution_time(routes)

        improved = neighborhoods[neighborhood_index](
            model,
            routes,
            neighbors_set_array
        )

        new_time = total_solution_time(routes)

        if improved and new_time < old_time - EPSILON:
            improved_at_least_once = True
            neighborhood_index = 0
        else:
            neighborhood_index += 1

    return improved_at_least_once
