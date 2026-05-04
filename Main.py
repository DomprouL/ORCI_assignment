import io
import sys
import Helpers
from Parser import load_model
from SolutionPlotter import plot_ctop_solution
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

    neighbors_list_array, neighbors_set_array = Helpers.build_nearest_neighbors_heap(model, k=80)

    print(f"Average demand: {avg_demand:.2f}")
    print(f"Average distance: {avg_distance:.2f}")

    print("\n--- Constructing Initial Solution ---")
    
    routes, visited, total_profit, total_time, used_routes = Helpers.multi_restart_initial_solution(
        model,
        avg_demand,
        avg_distance,
        neighbors_set_array,
        restarts=3,
        top_k=5,
        seed=23
    )

    print("\n--- Initial Solution ---")

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