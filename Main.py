import io
import sys
import Helpers
from Parser import load_model
from SolutionPlotter import plot_ctop_solution
from Time_Operators import time_vnd, total_solution_time, total_solution_profit
from SolutionValidator import validate_solution
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import random
from Destroy_Operators import shaw_removal

def main(instance_file):
    model = load_model(instance_file)

    avg_demand = Helpers.compute_average_demand(model)
    avg_distance = Helpers.compute_average_distance(model)

    neighbors_list_array, neighbors_set_array = Helpers.build_nearest_neighbors_heap(
        model,
        k=100
    )

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

    iteration = 0

    while True:
        iteration += 1

        old_profit = total_solution_profit(routes)
        old_time = total_solution_time(routes)

        # Step 1: compress current routes using time operators
        time_improved = time_vnd(model, routes, neighbors_set_array)

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
            break

        before_insert_profit = total_solution_profit(routes)
        before_insert_time = total_solution_time(routes)

        Helpers.insert_node(model, best_route, node, position, added_time)
        visited.add(node)

        after_insert_profit = total_solution_profit(routes)
        after_insert_time = total_solution_time(routes)

    total_profit, total_time, used_routes = Helpers.compute_solution_totals(routes)

    routes_for_plot = [route.nodes for route in routes]

    plot_ctop_solution(model, routes_for_plot)


    valid, report = validate_solution(model, routes_for_plot, enforce_mandatory=False)
    if valid:
        print("\n✅ Solution is VALID.")
        print(f"🏆 Total Profit Collected: {report['total_profit']}")
        print("\nRoute Details:")
        for i, (load, cost, profit) in enumerate(zip(report['route_loads'], report['route_costs'], report['route_profits'])):
            print(f"Route {i} -> Load = {load}/{model.capacity}, Time = {cost:.2f}/{model.t_max}, Profit = {profit}")

        rng = random.Random(4)

        removed_nodes = shaw_removal(
            model,
            routes,
            visited,
            rng,
            enforce_mandatory=True,
            remove_count=8
        )

        print("\n--- Destroy test ---")
        print(f"Removed nodes: {removed_nodes}")

        print("\nPartial solution after destroy:")
        for idx, route in enumerate(routes):
            print(f"Route {idx}: {route.nodes}")
            print(f"  Load: {route.load}/{model.capacity}")
            print(f"  Time: {route.time:.2f}/{model.t_max}")
            print(f"  Profit: {route.profit}")

        print(f"\nVisited customers after destroy: {len(visited)}")
    else:
        print("\n❌ Solution is INVALID.")
        print("Errors Found:")
        for error in report['errors']:
            print(f" - {error}")


if __name__ == "__main__":
    main("ctop_main_instance.txt")