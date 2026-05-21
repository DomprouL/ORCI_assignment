import io
import sys

import Helpers
from Parser import load_model
from SolutionPlotter import plot_ctop_solution
from Time_Operators import time_vnd, total_solution_time, total_solution_profit

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def main(instance_file):
    print(f"Loading Instance: '{instance_file}'...")
    model = load_model(instance_file)

    print("\n--- Model Summary ---")
    print(f"Number of nodes: {model.num_nodes} (including depot)")
    print(f"Vehicle capacity (Q): {model.capacity}")
    print(f"Number of vehicles (K): {model.vehicles}")
    print(f"Time limit per route (T_max): {model.t_max}")

    avg_demand = Helpers.compute_average_demand(model)
    avg_distance = Helpers.compute_average_distance(model)

    neighbors_list_array, neighbors_set_array = Helpers.build_nearest_neighbors_heap(
        model,
        k=100
    )

    print(f"Average demand: {avg_demand:.2f}")
    print(f"Average distance: {avg_distance:.2f}")

    print("\n--- Constructing Initial Solution ---")

    routes, visited, initial_profit, initial_time, initial_used_routes = (
        Helpers.multi_restart_initial_solution(
            model,
            avg_demand,
            avg_distance,
            neighbors_set_array,
            restarts=30,
            top_k=5,
            seed=4
        )
    )

    print("\n--- Initial Solution Before Local Search ---")
    print(f"Total profit: {initial_profit}")
    print(f"Total time: {initial_time:.2f}")
    print(f"Used routes: {initial_used_routes}/{model.vehicles}")
    print(f"Visited customers: {len(visited)}")

    iteration = 0

    while True:
        iteration += 1

        old_profit = total_solution_profit(routes)
        old_time = total_solution_time(routes)

        # Step 1: compress current routes using time operators
        time_improved = time_vnd(model, routes)

        after_vnd_profit = total_solution_profit(routes)
        after_vnd_time = total_solution_time(routes)

        best_route, node, position, added_time, score = Helpers.find_best_global_insertion(
            model,
            routes,
            visited,
            avg_demand,
            avg_distance,
            neighbors_set_array,
            top_k=1
        )

        if node is None:
            print(f"Iteration {iteration}: no more feasible insertion.")
            break

        before_insert_profit = total_solution_profit(routes)
        before_insert_time = total_solution_time(routes)

        Helpers.insert_node(model, best_route, node, position, added_time)
        visited.add(node)

        after_insert_profit = total_solution_profit(routes)
        after_insert_time = total_solution_time(routes)

        print(
            f"Iteration {iteration}: inserted node {node}, "
            f"profit {before_insert_profit} -> {after_insert_profit}, "
            f"time {before_insert_time:.2f} -> {after_insert_time:.2f}, "
            f"added_time={added_time:.2f}, score={score:.2f}"
        )

    # Final recomputation after all improvements
    total_profit, total_time, used_routes = Helpers.compute_solution_totals(routes)

    print("Solution After Time Improvements and Insertions:")
    print(f"Total profit: {total_profit}")
    print(f"Total time: {total_time:.2f}")
    print(f"Used routes: {used_routes}/{model.vehicles}")
    print(f"Visited customers: {len(visited)}")

    print("\nRoute Details:")
    for idx, route in enumerate(routes):
        print(f"\nRoute {idx + 1}: {route.nodes}")
        print(f"  Load: {route.load}/{model.capacity}")
        print(f"  Time: {route.time:.2f}/{model.t_max}")
        print(f"  Profit: {route.profit}")

    routes_for_plot = [route.nodes for route in routes]

    plot_ctop_solution(model, routes_for_plot)

if __name__ == "__main__":
    main("ctop_main_instance.txt")