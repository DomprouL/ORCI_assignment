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

#Computes the total profit of a route based on the sequence of nodes.
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

# Checks if a route starts and ends with the depot (node 0) and has at least one customer.
def is_route_structure_valid(route):
    if len(route.nodes) < 2:
        return False

    if route.nodes[0] != 0:
        return False

    if route.nodes[-1] != 0:
        return False

    return True

# Checks if a route is feasible with respect to:
# - depot structure
# - capacity
# - maximum route time
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

# Changes route's sequence of nodes to new_nodes. Then updates the route's time, load, and profit accordingly.
def apply_new_nodes_to_route(model, route, new_nodes):
    route.nodes = new_nodes
    update_route_values(model, route)

# intra 2-opt
def intra_2opt_best_improvement(model, route):
    if len(route.nodes) <= 4:
        return False

    old_time = route.time
    best_time = old_time
    best_nodes = None

    nodes = route.nodes

    for i in range(1, len(nodes) - 2):
        for j in range(i + 1, len(nodes) - 1):

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

# intra relocate 1-0
def intra_relocate_best_improvement(model, route):
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

#intra swap 1-1
def intra_swap_best_improvement(model, route):
    if len(route.nodes) <= 3:
        return False

    old_time = route.time
    best_time = old_time
    best_nodes = None

    nodes = route.nodes

    for i in range(1, len(nodes) - 2):
        for j in range(i + 1, len(nodes) - 1):

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

#inter relocate 1-0 between two routes
def inter_relocate_best_improvement(model, route_a, route_b):

    old_total_time = route_a.time + route_b.time
    best_total_time = old_total_time
    best_nodes_a = None
    best_nodes_b = None

    for remove_pos in range(1, len(route_a.nodes) - 1):

        customer = route_a.nodes[remove_pos]

        new_nodes_a = route_a.nodes[:remove_pos] + route_a.nodes[remove_pos + 1:]

        for insert_pos in range(1, len(route_b.nodes)):

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

    for remove_pos in range(1, len(route_b.nodes) - 1):

        customer = route_b.nodes[remove_pos]

        new_nodes_b = route_b.nodes[:remove_pos] + route_b.nodes[remove_pos + 1:]

        for insert_pos in range(1, len(route_a.nodes)):

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

# inter swap 1-1 between two routes
def inter_swap_best_improvement(model, route_a, route_b):

    old_total_time = route_a.time + route_b.time
    best_total_time = old_total_time
    best_nodes_a = None
    best_nodes_b = None

    for pos_a in range(1, len(route_a.nodes) - 1):
        for pos_b in range(1, len(route_b.nodes) - 1):

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

# inter 2-opt between two routes
def inter_2opt_best_improvement(model, route_a, route_b):

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

# intra 2opt VND part, works as long as it finds an improving move.
def intra_2opt_local_search(model, route):

    improved_at_least_once = False

    while True:
        improved = intra_2opt_best_improvement(model, route)

        if not improved:
            break

        improved_at_least_once = True

    return improved_at_least_once

# intra relocation VND part, works as long as it finds an improving move.
def intra_relocate_local_search(model, route):
    improved_at_least_once = False

    while True:
        improved = intra_relocate_best_improvement(model, route)

        if not improved:
            break

        improved_at_least_once = True

    return improved_at_least_once

# intra swap VND part, works as long as it finds an improving move.
def intra_swap_local_search(model, route):

    improved_at_least_once = False

    while True:
        improved = intra_swap_best_improvement(model, route)

        if not improved:
            break

        improved_at_least_once = True

    return improved_at_least_once

# inter 2opt VND part, works as long as it finds an improving move.
def inter_2opt_local_search(model, routes):

    improved_at_least_once = False

    while True:
        improved_in_iteration = False

        for i in range(len(routes) - 1):
            for j in range(i + 1, len(routes)):

                improved = inter_2opt_best_improvement(model, routes[i], routes[j])

                if improved:
                    improved_at_least_once = True
                    improved_in_iteration = True

        if not improved_in_iteration:
            break

    return improved_at_least_once

# inter relocation VND part, works as long as it finds an improving move.
def inter_relocate_local_search(model, routes):

    improved_at_least_once = False

    while True:
        improved_in_iteration = False

        for i in range(len(routes) - 1):
            for j in range(i + 1, len(routes)):

                improved = inter_relocate_best_improvement(model, routes[i], routes[j])

                if improved:
                    improved_at_least_once = True
                    improved_in_iteration = True

        if not improved_in_iteration:
            break

    return improved_at_least_once

# inter swap VND part, works as long as it finds an improving move.
def inter_swap_local_search(model, routes):

    improved_at_least_once = False

    while True:
        improved_in_iteration = False

        for i in range(len(routes) - 1):
            for j in range(i + 1, len(routes)):

                improved = inter_swap_best_improvement(model, routes[i], routes[j])

                if improved:
                    improved_at_least_once = True
                    improved_in_iteration = True

        if not improved_in_iteration:
            break

    return improved_at_least_once

# Applies intra 2-opt to all routes.
def intra_2opt_all_routes_local_search(model, routes):
    improved_at_least_once = False

    for route in routes:
        improved = intra_2opt_local_search(model, route)

        if improved:
            improved_at_least_once = True

    return improved_at_least_once


# Applies intra relocate to all routes.
def intra_relocate_all_routes_local_search(model, routes):
    improved_at_least_once = False

    for route in routes:
        improved = intra_relocate_local_search(model, route)

        if improved:
            improved_at_least_once = True

    return improved_at_least_once


# Applies intra swap to all routes.
def intra_swap_all_routes_local_search(model, routes):
    improved_at_least_once = False

    for route in routes:
        improved = intra_swap_local_search(model, route)

        if improved:
            improved_at_least_once = True

    return improved_at_least_once

#VND that applies the 6 time operators in sequence until no improvement is found in any of them.
# VND that applies the time operators in sequence until no improvement is found.
def time_vnd(model, routes):
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

        improved = neighborhoods[neighborhood_index](model, routes)

        new_time = total_solution_time(routes)

        if improved and new_time < old_time - EPSILON:
            improved_at_least_once = True
            neighborhood_index = 0
        else:
            neighborhood_index += 1

    return improved_at_least_once