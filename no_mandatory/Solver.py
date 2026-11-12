"""Run the Standard CTOP construction and improvement phases."""
from . import Helpers
from .Capacity_Repair import (
    capacity_destroy_repair_search_sa,
    repair_solution_with_insertions,
    warm_start_remove_insert_loop,
)
from .Time_Operators import time_vnd


def solve_standard(model):
    avg_demand = Helpers.compute_average_demand(model)
    avg_distance = Helpers.compute_average_distance(model)

    _, neighbors_set_array = Helpers.build_nearest_neighbors_heap(
        model,
        k=100
    )

    # ------------------------------------------------------------
    # 1. Construct initial solution using multi-start
    # ------------------------------------------------------------
    routes, visited, _, _, _ = (
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

    # ------------------------------------------------------------
    # 3. Capacity-focused destroy-repair search
    # ------------------------------------------------------------

    routes, visited, _, _ = capacity_destroy_repair_search_sa(
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
    for _ in range(5):
        before_profit, _, _ = Helpers.compute_solution_totals(routes)

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

        after_profit, _, _ = Helpers.compute_solution_totals(routes)

        if inserted == 0 and after_profit == before_profit:
            break

    return routes
