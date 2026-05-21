# Destroy_Operators.py

from Time_Operators import update_route_values

EPSILON = 1e-6


# Computes profit / demand once for every node.
# Higher value = better node.
# Lower value = worse node, more likely to be removed.
def build_profit_density(model):
    profit_density = {}

    for node in model.nodes:
        if node.id == 0:
            continue

        if node.demand <= 0:
            profit_density[node.id] = float("inf")
        else:
            profit_density[node.id] = node.profit / node.demand

    return profit_density


# Checks whether a node is allowed to be removed.
# If enforce_mandatory=True, mandatory nodes are protected.
def is_removable_node(model, node_id, enforce_mandatory):
    if node_id == 0:
        return False

    if enforce_mandatory and model.nodes[node_id].isMandatory:
        return False

    return True


# Returns removable customer node IDs from a route.
def get_removable_nodes_in_route(model, route, enforce_mandatory):
    removable_nodes = []

    for node_id in route.nodes:
        if is_removable_node(model, node_id, enforce_mandatory):
            removable_nodes.append(node_id)

    return removable_nodes


# Returns all removable routed customer node IDs from the whole solution.
def get_all_removable_routed_nodes(model, routes, enforce_mandatory):
    removable_nodes = []

    for route in routes:
        for node_id in route.nodes:
            if is_removable_node(model, node_id, enforce_mandatory):
                removable_nodes.append(node_id)

    return removable_nodes


# Removes a set of nodes from the solution.
# Removed nodes become unrouted immediately, so they are removed from visited.
def remove_nodes_from_solution(model, routes, visited, nodes_to_remove):
    nodes_to_remove = set(nodes_to_remove)
    actually_removed = []

    for route in routes:
        old_nodes = route.nodes
        new_nodes = []

        route_changed = False

        for node_id in old_nodes:
            if node_id != 0 and node_id in nodes_to_remove:
                route_changed = True
                actually_removed.append(node_id)

                if node_id in visited:
                    visited.remove(node_id)
            else:
                new_nodes.append(node_id)

        if route_changed:
            route.nodes = new_nodes
            update_route_values(model, route)

    return actually_removed


# Weighted sampling without replacement.
def weighted_sample_without_replacement(items, weights, k, rng):
    selected = []

    items = list(items)
    weights = list(weights)

    k = min(k, len(items))

    for _ in range(k):
        if not items:
            break

        total_weight = sum(weights)

        if total_weight <= 0:
            chosen_index = rng.randrange(len(items))
        else:
            chosen_index = rng.choices(
                range(len(items)),
                weights=weights,
                k=1
            )[0]

        selected.append(items.pop(chosen_index))
        weights.pop(chosen_index)

    return selected


# Selects one route using time-slack-biased probabilities.
# Route with largest time slack gets largest weight.
def select_route_by_time_slack(model, routes, rng, enforce_mandatory):
    candidate_routes = []

    for route in routes:
        removable_nodes = get_removable_nodes_in_route(
            model,
            route,
            enforce_mandatory
        )

        if len(removable_nodes) > 0:
            candidate_routes.append(route)

    if not candidate_routes:
        return None

    # Larger slack = worse route = higher priority.
    candidate_routes.sort(
        key=lambda route: model.t_max - route.time,
        reverse=True
    )

    n = len(candidate_routes)

    # Example for 5 routes: [5, 4, 3, 2, 1]
    weights = list(range(n, 0, -1))

    selected_route = rng.choices(
        candidate_routes,
        weights=weights,
        k=1
    )[0]

    return selected_route


# 1st destroy operator:
# Selects a route with probability biased toward high time slack.
# Removes 50% of its removable nodes, specifically the worst profit/demand nodes.
def slack_biased_route_destroy(
    model,
    routes,
    visited,
    profit_density,
    rng,
    enforce_mandatory=False,
    destroy_fraction=0.5,
    min_removed=1,
    max_removed=None
):
    selected_route = select_route_by_time_slack(
        model,
        routes,
        rng,
        enforce_mandatory
    )

    if selected_route is None:
        return []

    removable_nodes = get_removable_nodes_in_route(
        model,
        selected_route,
        enforce_mandatory
    )

    if not removable_nodes:
        return []

    number_to_remove = int(len(removable_nodes) * destroy_fraction)

    number_to_remove = max(min_removed, number_to_remove)
    number_to_remove = min(number_to_remove, len(removable_nodes))

    if max_removed is not None:
        number_to_remove = min(number_to_remove, max_removed)

    # Worst nodes = lowest profit / demand.
    removable_nodes.sort(
        key=lambda node_id: profit_density.get(node_id, float("inf"))
    )

    nodes_to_remove = removable_nodes[:number_to_remove]

    removed_nodes = remove_nodes_from_solution(
        model,
        routes,
        visited,
        nodes_to_remove
    )

    return removed_nodes


# 2nd destroy operator:
# Removes a random number of routed nodes between min_remove and max_remove.
# Selection is weighted toward bad profit/demand nodes.
def random_worst_removal(
    model,
    routes,
    visited,
    profit_density,
    rng,
    enforce_mandatory=False,
    min_remove=10,
    max_remove=20
):
    removable_nodes = get_all_removable_routed_nodes(
        model,
        routes,
        enforce_mandatory
    )

    if not removable_nodes:
        return []

    number_to_remove = rng.randint(min_remove, max_remove)
    number_to_remove = min(number_to_remove, len(removable_nodes))

    weights = []

    for node_id in removable_nodes:
        density = profit_density.get(node_id, float("inf"))

        if density == float("inf"):
            weight = 0.0
        else:
            weight = 1.0 / (density + EPSILON)

        weights.append(weight)

    nodes_to_remove = weighted_sample_without_replacement(
        removable_nodes,
        weights,
        number_to_remove,
        rng
    )

    removed_nodes = remove_nodes_from_solution(
        model,
        routes,
        visited,
        nodes_to_remove
    )

    return removed_nodes


# Helper for SISR:
# Creates one random removable string from a route.
def sample_string_from_route(
    model,
    route,
    rng,
    enforce_mandatory,
    min_string_length,
    max_string_length
):
    customer_positions = list(range(1, len(route.nodes) - 1))

    if len(customer_positions) < min_string_length:
        return None

    max_possible_length = min(max_string_length, len(customer_positions))

    if max_possible_length < min_string_length:
        return None

    string_length = rng.randint(min_string_length, max_possible_length)

    first_possible_start = 1
    last_possible_start = len(route.nodes) - 1 - string_length

    if last_possible_start < first_possible_start:
        return None

    start_pos = rng.randint(first_possible_start, last_possible_start)
    end_pos = start_pos + string_length

    string_nodes = route.nodes[start_pos:end_pos]

    for node_id in string_nodes:
        if not is_removable_node(model, node_id, enforce_mandatory):
            return None

    return string_nodes


# Computes profit/demand density of a string.
# Lower density = worse string.
def compute_string_density(model, string_nodes):
    total_profit = 0
    total_demand = 0

    for node_id in string_nodes:
        total_profit += model.nodes[node_id].profit
        total_demand += model.nodes[node_id].demand

    if total_demand <= 0:
        return float("inf")

    return total_profit / total_demand


# 3rd destroy operator:
# Sampled SISR.
# Samples random strings from slack-biased routes and removes the worst string.
def sampled_sisr_removal(
    model,
    routes,
    visited,
    rng,
    enforce_mandatory=False,
    sample_count=20,
    min_string_length=2,
    max_string_length=5
):
    candidate_strings = []

    attempts = 0
    max_attempts = sample_count * 5

    while len(candidate_strings) < sample_count and attempts < max_attempts:
        attempts += 1

        selected_route = select_route_by_time_slack(
            model,
            routes,
            rng,
            enforce_mandatory
        )

        if selected_route is None:
            break

        string_nodes = sample_string_from_route(
            model,
            selected_route,
            rng,
            enforce_mandatory,
            min_string_length,
            max_string_length
        )

        if string_nodes is None:
            continue

        string_density = compute_string_density(model, string_nodes)

        candidate_strings.append((string_density, string_nodes))

    if not candidate_strings:
        return []

    # Worst string = lowest profit / demand density.
    candidate_strings.sort(key=lambda x: x[0])

    worst_string_density, nodes_to_remove = candidate_strings[0]

    removed_nodes = remove_nodes_from_solution(
        model,
        routes,
        visited,
        nodes_to_remove
    )

    return removed_nodes


# 4th destroy operator:
# Shaw / cluster removal using distance only.
# Picks a random seed and removes the closest routed nodes to it.
def shaw_removal(
    model,
    routes,
    visited,
    rng,
    enforce_mandatory=False,
    remove_count=8
):
    removable_nodes = get_all_removable_routed_nodes(
        model,
        routes,
        enforce_mandatory
    )

    if not removable_nodes:
        return []

    remove_count = min(remove_count, len(removable_nodes))

    seed_node = rng.choice(removable_nodes)

    # Sort all removable nodes by distance from the seed.
    removable_nodes.sort(
        key=lambda node_id: model.cost_matrix[seed_node][node_id]
    )

    nodes_to_remove = removable_nodes[:remove_count]

    removed_nodes = remove_nodes_from_solution(
        model,
        routes,
        visited,
        nodes_to_remove
    )

    return removed_nodes