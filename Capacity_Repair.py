import copy
import random
import math
import random
import Helpers
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

def simulated_annealing_acceptance(
    trial_profit,
    trial_time,
    current_profit,
    current_time,
    temperature
):
    """
    Simulated annealing acceptance rule.

    Profit is the primary objective.
    Time is used only as a tie-breaker when profit is equal.
    """

    if solution_is_better(
        trial_profit,
        trial_time,
        current_profit,
        current_time
    ):
        return True

    profit_delta = trial_profit - current_profit

    if profit_delta < 0:
        probability = math.exp(profit_delta / temperature)
        return random.random() < probability

    if profit_delta == 0 and trial_time > current_time:
        time_delta = trial_time - current_time
        probability = math.exp(-time_delta / temperature)
        return random.random() < probability

    return False


def get_worst_profit_demand_nodes(
    model,
    routes,
    pool_size=30,
    protect_mandatory=False
):
    """
    Returns the worst served nodes according to profit / demand.
    Lower ratio means worse use of vehicle capacity.
    """

    candidates = []

    for route_idx, route in enumerate(routes):
        for node_id in route.nodes[1:-1]:

            if node_id == 0:
                continue

            if protect_mandatory and model.nodes[node_id].isMandatory:
                continue

            demand = model.nodes[node_id].demand
            profit = model.nodes[node_id].profit

            if demand <= 0:
                continue

            ratio = profit / demand

            candidates.append((ratio, node_id, route_idx))

    candidates.sort(key=lambda x: x[0])

    return candidates[:pool_size]


def remove_nodes_from_routes(model, routes, visited, node_ids_to_remove):
    """
    Removes selected nodes from their routes and updates route values.
    """

    node_ids_to_remove = set(node_ids_to_remove)

    for route in routes:
        old_len = len(route.nodes)

        route.nodes = [
            node_id
            for node_id in route.nodes
            if node_id not in node_ids_to_remove
        ]

        if len(route.nodes) != old_len:
            update_route_values(model, route)

    for node_id in node_ids_to_remove:
        visited.discard(node_id)


def repair_solution_with_insertions(
    model,
    routes,
    visited,
    avg_demand,
    avg_distance,
    neighbors_set_array,
    top_k=3,
    max_insertions=1000
):
    """
    Greedily inserts feasible nodes until no more feasible insertion exists.
    """

    inserted_count = 0

    while inserted_count < max_insertions:

        best_route, node, position, added_time, score = Helpers.find_best_global_insertion(
            model,
            routes,
            visited,
            avg_demand,
            avg_distance,
            neighbors_set_array,
            top_k=top_k
        )

        if node is None:
            break

        Helpers.insert_node(model, best_route, node, position, added_time)
        visited.add(node)
        inserted_count += 1

    return inserted_count


def warm_start_remove_insert_loop(
    model,
    routes,
    visited,
    avg_demand,
    avg_distance,
    neighbors_set_array,
    top_k=1,
    protect_mandatory=False
):
    """
    Keeps your existing first idea:
    remove the worst profit/demand node once,
    then repeatedly apply VND and insertion.
    """

    worst_nodes = get_worst_profit_demand_nodes(
        model,
        routes,
        pool_size=1,
        protect_mandatory=protect_mandatory
    )

    if worst_nodes:
        worst_ratio, worst_node_id, _ = worst_nodes[0]

        worst_profit = model.nodes[worst_node_id].profit
        worst_demand = model.nodes[worst_node_id].demand

        remove_nodes_from_routes(
            model,
            routes,
            visited,
            [worst_node_id]
        )

        print(
            f"\nRemoved worst node: {worst_node_id} | "
            f"Profit = {worst_profit} | "
            f"Demand = {worst_demand} | "
            f"Profit/Demand = {worst_ratio:.4f}",
            flush=True
        )
    else:
        print("\nNo removable customer node found.", flush=True)

    iteration = 0

    while True:
        iteration += 1

        old_profit = total_solution_profit(routes)
        old_time = total_solution_time(routes)

        print(
            f"\nIteration {iteration} | "
            f"Before VND: Profit = {old_profit}, Time = {old_time:.2f}",
            flush=True
        )

        time_improved = time_vnd(model, routes, neighbors_set_array)

        after_vnd_profit = total_solution_profit(routes)
        after_vnd_time = total_solution_time(routes)

        print(
            f"After VND: Profit = {after_vnd_profit}, "
            f"Time = {after_vnd_time:.2f}, "
            f"Improved = {time_improved}",
            flush=True
        )

        best_route, node, position, added_time, score = Helpers.find_best_global_insertion(
            model,
            routes,
            visited,
            avg_demand,
            avg_distance,
            neighbors_set_array,
            top_k=top_k
        )

        if node is None:
            print("\nNo more feasible insertions found.")
            break

        before_insert_profit = total_solution_profit(routes)
        before_insert_time = total_solution_time(routes)

        Helpers.insert_node(model, best_route, node, position, added_time)
        visited.add(node)

        after_insert_profit = total_solution_profit(routes)
        after_insert_time = total_solution_time(routes)

        print(
            f"Inserted node: {node} | "
            f"Profit = {model.nodes[node].profit} | "
            f"Demand = {model.nodes[node].demand} | "
            f"Added Time = {added_time:.2f} | "
            f"Score = {score:.4f}",
            flush=True
        )

        print(
            f"After insertion: Profit {before_insert_profit} -> {after_insert_profit}, "
            f"Time {before_insert_time:.2f} -> {after_insert_time:.2f}",
            flush=True
        )


def capacity_destroy_repair_search_sa(
    model,
    routes,
    visited,
    avg_demand,
    avg_distance,
    neighbors_set_array,
    iterations=1000,
    remove_min=1,
    remove_max=7,
    bad_pool_size=30,
    insertion_top_k=3,
    seed=4,
    protect_mandatory=False,
    use_vnd=True,
    start_temperature=80.0,
    end_temperature=1.0
):
    """
    Capacity-focused destroy-repair with simulated annealing acceptance.

    Difference from the normal version:
    - Better solutions are always accepted.
    - Worse solutions may be accepted with a probability.
    - The probability decreases as temperature decreases.
    """

    random.seed(seed)

    current_routes = copy.deepcopy(routes)
    current_visited = set(visited)

    current_profit = total_solution_profit(current_routes)
    current_time = total_solution_time(current_routes)

    best_routes = copy.deepcopy(current_routes)
    best_visited = set(current_visited)
    best_profit = current_profit
    best_time = current_time

    print("\nStarting capacity destroy-repair search with Simulated Annealing.")
    print(f"Start Profit = {best_profit}, Start Time = {best_time:.2f}")

    for iteration in range(1, iterations + 1):

        temperature = start_temperature / math.log(iteration + 2)

        if temperature < end_temperature:
            temperature = end_temperature

        trial_routes = copy.deepcopy(current_routes)
        trial_visited = set(current_visited)

        worst_pool = get_worst_profit_demand_nodes(
            model,
            trial_routes,
            pool_size=bad_pool_size,
            protect_mandatory=protect_mandatory
        )

        if not worst_pool:
            break

        max_possible_remove = min(remove_max, len(worst_pool))
        min_possible_remove = min(remove_min, max_possible_remove)

        remove_count = random.randint(min_possible_remove, max_possible_remove)

        selected = random.sample(worst_pool, remove_count)
        nodes_to_remove = [node_id for _, node_id, _ in selected]

        old_trial_profit = total_solution_profit(trial_routes)
        old_trial_time = total_solution_time(trial_routes)

        remove_nodes_from_routes(
            model,
            trial_routes,
            trial_visited,
            nodes_to_remove
        )

        if use_vnd:
            time_vnd(model, trial_routes, neighbors_set_array)

        inserted_count = repair_solution_with_insertions(
            model,
            trial_routes,
            trial_visited,
            avg_demand,
            avg_distance,
            neighbors_set_array,
            top_k=insertion_top_k
        )

        if use_vnd:
            time_vnd(model, trial_routes, neighbors_set_array)

            repair_solution_with_insertions(
                model,
                trial_routes,
                trial_visited,
                avg_demand,
                avg_distance,
                neighbors_set_array,
                top_k=insertion_top_k
            )

        trial_profit = total_solution_profit(trial_routes)
        trial_time = total_solution_time(trial_routes)

        accepted = simulated_annealing_acceptance(
            trial_profit,
            trial_time,
            current_profit,
            current_time,
            temperature
        )

        if accepted:
            accepted_because = "IMPROVING"

            if not solution_is_better(
                trial_profit,
                trial_time,
                current_profit,
                current_time
            ):
                accepted_because = "SA-WORSE"

            current_routes = trial_routes
            current_visited = trial_visited
            current_profit = trial_profit
            current_time = trial_time

            print(
                f"[ACCEPT-{accepted_because}] Iter {iteration} | "
                f"T = {temperature:.4f} | "
                f"Removed = {nodes_to_remove} | "
                f"Inserted = {inserted_count} | "
                f"Profit {old_trial_profit} -> {trial_profit} | "
                f"Time {old_trial_time:.2f} -> {trial_time:.2f}",
                flush=True
            )

        if solution_is_better(
            current_profit,
            current_time,
            best_profit,
            best_time
        ):
            best_routes = copy.deepcopy(current_routes)
            best_visited = set(current_visited)
            best_profit = current_profit
            best_time = current_time

            print(
                f"  >>> NEW BEST: Profit = {best_profit}, "
                f"Time = {best_time:.2f}",
                flush=True
            )

        if iteration % 25 == 0:
            print(
                f"Iter {iteration} | "
                f"T = {temperature:.4f} | "
                f"Current Profit = {current_profit}, "
                f"Best Profit = {best_profit}, "
                f"Best Time = {best_time:.2f}",
                flush=True
            )

    return best_routes, best_visited, best_profit, best_time
