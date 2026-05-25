import io
import sys

import Helpers
from Parser import load_model
from SolutionPlotter import plot_ctop_solution
from SolutionValidator import validate_solution
from Capacity_Repair import (
    warm_start_remove_insert_loop,
    capacity_destroy_repair_search
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def print_route_details(model, routes):
    print("\nRoute Details:")

    for i, route in enumerate(routes):
        if len(route.nodes) <= 2:
            continue

        print(
            f"Route {i} -> "
            f"Load = {route.load}/{model.capacity}, "
            f"Time = {route.time:.2f}/{model.t_max}, "
            f"Profit = {route.profit}"
        )


def main(instance_file):
   
    model = load_model(instance_file)

    avg_demand = Helpers.compute_average_demand(model)
    avg_distance = Helpers.compute_average_distance(model)

    neighbors_list_array, neighbors_set_array = Helpers.build_nearest_neighbors_heap(
        model,
        k=100
    )

    # ------------------------------------------------------------
    # 4. Construct initial solution using multi-start
    # ------------------------------------------------------------
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

    print("\nInitial solution created.")
    print(f"Initial Profit = {initial_profit}")
    print(f"Initial Time = {initial_time:.2f}")
    print(f"Initial Used Routes = {initial_used_routes}")

    print_route_details(model, routes)

    # ------------------------------------------------------------
    # 5. Warm-start improvement
    #
    # This keeps your existing logic:
    # - remove the worst profit/demand node once
    # - run VND
    # - insert feasible nodes
    # - repeat until no more feasible insertion exists
    # ------------------------------------------------------------
    warm_start_remove_insert_loop(
        model,
        routes,
        visited,
        avg_demand,
        avg_distance,
        neighbors_set_array,
        top_k=1,
        protect_mandatory=False
    )

    warm_profit, warm_time, warm_used_routes = Helpers.compute_solution_totals(routes)

    print("\nAfter warm-start remove/insert loop:")
    print(f"Profit = {warm_profit}")
    print(f"Time = {warm_time:.2f}")
    print(f"Used Routes = {warm_used_routes}")

    print_route_details(model, routes)

    # ------------------------------------------------------------
    # 6. Capacity-focused destroy-repair search
    #
    # Since capacity is the binding constraint, this tries to:
    # - remove low profit/demand nodes
    # - refill capacity with better nodes
    # - accept only improving solutions
    # ------------------------------------------------------------
    routes, visited, best_profit, best_time = capacity_destroy_repair_search(
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
        use_vnd= False
    )

    # ------------------------------------------------------------
    # 7. Final totals
    # ------------------------------------------------------------
    total_profit, total_time, used_routes = Helpers.compute_solution_totals(routes)

    print("\nFinal Solution Totals:")
    print(f"Total Profit = {total_profit}")
    print(f"Total Time = {total_time:.2f}")
    print(f"Used Routes = {used_routes}")

    print_route_details(model, routes)

    
    routes_for_plot = [route.nodes for route in routes]

    plot_ctop_solution(model, routes_for_plot)

    valid, report = validate_solution(
        model,
        routes_for_plot,
        enforce_mandatory=False
    )

    if valid:
        print("\n✅ Solution is VALID.")
        print(f"🏆 Total Profit Collected: {report['total_profit']}")
        print("\nRoute Details:")

        for i, (load, cost, profit) in enumerate(
            zip(report['route_loads'], report['route_costs'], report['route_profits'])
        ):
            print(
                f"Route {i} -> "
                f"Load = {load}/{model.capacity}, "
                f"Time = {cost:.2f}/{model.t_max}, "
                f"Profit = {profit}"
            )

    else:
        print("\n❌ Solution is INVALID.")
        print("Errors Found:")

        for error in report['errors']:
            print(f" - {error}")


if __name__ == "__main__":
    main("ctop_main_instance.txt")