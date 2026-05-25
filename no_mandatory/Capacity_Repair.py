
import copy
import random
import math
from Time_Operators import (
    time_vnd,
    total_solution_time,
    total_solution_profit,
    update_route_values
)

EPSILON = 1e-6

def solution_is_better(new_profit, new_time, old_profit, old_time):
    if new_profit > old_profit:
        return True
    if new_profit == old_profit and new_time < old_time - EPSILON:
        return True
    return False

def simulated_annealing_acceptance(trial_profit, trial_time, current_profit, current_time, temperature):
    if solution_is_better(trial_profit, trial_time, current_profit, current_time):
        return True
    profit_delta = trial_profit - current_profit
    if profit_delta < 0:
        return random.random() < math.exp(profit_delta / temperature)
    if profit_delta == 0 and trial_time > current_time:
        return random.random() < math.exp(-(trial_time - current_time) / temperature)
    return False

def get_worst_profit_demand_nodes(model, routes, pool_size=30, protect_mandatory=False):
    candidates = []
    for route_idx, route in enumerate(routes):
        for node_id in route.nodes[1:-1]:
            if node_id == 0 or (protect_mandatory and model.nodes[node_id].isMandatory):
                continue
            demand = model.nodes[node_id].demand
            profit = model.nodes[node_id].profit
            if demand <= 0:
                continue
            candidates.append((profit / demand, node_id, route_idx))
    candidates.sort(key=lambda x: x[0])
    return candidates[:pool_size]

def remove_nodes_from_routes(model, routes, visited, node_ids_to_remove):
    node_ids_to_remove = set(node_ids_to_remove)
    for route in routes:
        old_len = len(route.nodes)
        route.nodes = [n for n in route.nodes if n not in node_ids_to_remove]
        if len(route.nodes) != old_len:
            update_route_values(model, route)
    for node_id in node_ids_to_remove:
        visited.discard(node_id)

# Προσθήκη παραμέτρου 'solver' και αλγοριθμικό binding
def repair_solution_with_insertions(
    model, routes, visited, avg_demand, avg_distance, neighbors_set_array,
    solver, top_k=3, max_insertions=1000
):
    inserted_count = 0
    while inserted_count < max_insertions:
        best_route, node, position, added_time, score = solver.find_best_global_insertion(
            routes, visited, top_k=top_k
        )
        if node is None:
            break
        solver.insert_node(best_route, node, position, added_time)
        visited.add(node)
        inserted_count += 1
    return inserted_count


def warm_start_remove_insert_loop(
    model, routes, visited, avg_demand, avg_distance, neighbors_set_array,
    solver, top_k=1, protect_mandatory=False
):
    worst_nodes = get_worst_profit_demand_nodes(model, routes, pool_size=1, protect_mandatory=protect_mandatory)
    if worst_nodes:
        _, worst_node_id, _ = worst_nodes[0]
        remove_nodes_from_routes(model, routes, visited, [worst_node_id])

    while True:
        time_vnd(model, routes, neighbors_set_array)
        best_route, node, position, added_time, score = solver.find_best_global_insertion(
            routes, visited, top_k=top_k
        )
        if node is None:
            break
        solver.insert_node(best_route, node, position, added_time)
        visited.add(node)


def capacity_destroy_repair_search_sa(
    model, routes, visited, avg_demand, avg_distance, neighbors_set_array,
    solver, iterations=100, remove_min=1, remove_max=7, bad_pool_size=30,
    insertion_top_k=3, seed=None, protect_mandatory=False, use_vnd=False,
    start_temperature=80.0, end_temperature=1.0
):
    if seed is not None:
        random.seed(seed)

    current_routes = copy.deepcopy(routes)
    current_visited = set(visited)
    current_profit = total_solution_profit(current_routes)
    current_time = total_solution_time(current_routes)

    best_routes = copy.deepcopy(current_routes)
    best_visited = set(current_visited)
    best_profit = current_profit
    best_time = current_time

    for iteration in range(1, iterations + 1):
        temperature = start_temperature / math.log(iteration + 2)
        if temperature < end_temperature:
            temperature = end_temperature

        trial_routes = copy.deepcopy(current_routes)
        trial_visited = set(current_visited)

        worst_pool = get_worst_profit_demand_nodes(model, trial_routes, pool_size=bad_pool_size, protect_mandatory=protect_mandatory)
        if not worst_pool:
            break

        max_possible_remove = min(remove_max, len(worst_pool))
        min_possible_remove = min(remove_min, max_possible_remove)
        remove_count = random.randint(min_possible_remove, max_possible_remove)

        selected = random.sample(worst_pool, remove_count)
        nodes_to_remove = [node_id for _, node_id, _ in selected]

        remove_nodes_from_routes(model, trial_routes, trial_visited, nodes_to_remove)

        repair_solution_with_insertions(
            model, trial_routes, trial_visited, avg_demand, avg_distance,
            neighbors_set_array, solver=solver, top_k=insertion_top_k
        )

        trial_profit = total_solution_profit(trial_routes)
        trial_time = total_solution_time(trial_routes)

        if simulated_annealing_acceptance(trial_profit, trial_time, current_profit, current_time, temperature):
            current_routes = trial_routes
            current_visited = trial_visited
            current_profit = trial_profit
            current_time = trial_time

        if solution_is_better(current_profit, current_time, best_profit, best_time):
            best_routes = copy.deepcopy(current_routes)
            best_visited = set(current_visited)
            best_profit = current_profit
            best_time = current_time

    return best_routes, best_visited, best_profit, best_time