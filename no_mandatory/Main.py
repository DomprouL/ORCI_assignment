import io
import sys

import Helpers
from Parser import load_model
from SolutionPlotter import plot_ctop_solution
from SolutionValidator import validate_solution

from Capacity_Repair import (
    warm_start_remove_insert_loop,
    repair_solution_with_insertions
)

from Time_Operators import time_vnd
from Capacity_Repair import capacity_destroy_repair_search_sa

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

def main(instance_file):

    model = load_model(instance_file)

    avg_demand = Helpers.compute_average_demand(model)
    avg_distance = Helpers.compute_average_distance(model)

    neighbors_list_array, neighbors_set_array = Helpers.build_nearest_neighbors_heap(
        model,
        k=100
    )

    # ------------------------------------------------------------
    # 1. Construct initial solution using multi-start
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

    # ------------------------------------------------------------
    # 2. Warm-start improvement
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

    # ------------------------------------------------------------
    # 3. Capacity-focused destroy-repair search
    # ------------------------------------------------------------

    routes, visited, best_profit, best_time = capacity_destroy_repair_search_sa(
            model,
            routes,
            visited,
            avg_demand,
            avg_distance,
            neighbors_set_array,
            iterations=100,
            remove_min=1,
            remove_max=7,
            bad_pool_size=30,
            insertion_top_k=3,
            seed=23,
            protect_mandatory=False,
            use_vnd=False,
            start_temperature=80.0,
            end_temperature=1.0
        )

    # ------------------------------------------------------------
    # 4. Final totals
    # ------------------------------------------------------------
    total_profit, total_time, used_routes = Helpers.compute_solution_totals(routes)

    for polish_iter in range(1, 6):
        before_profit, before_time, _ = Helpers.compute_solution_totals(routes)

        time_vnd(
            model,
            routes,
            neighbors_set_array
        )

        inserted = repair_solution_with_insertions(
            model,
            routes,
            visited,
            avg_demand,
            avg_distance,
            neighbors_set_array,
            top_k=1
        )

        after_profit, after_time, _ = Helpers.compute_solution_totals(routes)

        if inserted == 0 and after_profit == before_profit:
            break

    # ------------------------------------------------------------
    # 6. Plot solution
    # ------------------------------------------------------------
    routes_for_plot = [route.nodes for route in routes]

    plot_ctop_solution(model, routes_for_plot)

    # ------------------------------------------------------------
    # 7. Validate solution
    # ------------------------------------------------------------
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

        for error in report["errors"]:
            print(f" - {error}")


if __name__ == "__main__":
    main("ctop_main_instance.txt")