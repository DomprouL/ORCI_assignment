import os
import sys
import io
from pathlib import Path

from Parser import load_model
from SolutionValidator import validate_solution, parse_solution_file
from SolutionPlotter import plot_ctop_solution

from Solver import Solver
from Helpers import write_solution_to_file

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')



def main(instance_file, solution_file, enforce_mandatory=True):
    current_folder = Path(__file__).resolve().parent
    instance_path = current_folder / instance_file
    solution_path = current_folder / solution_file

    print(f"Loading Instance: '{instance_path}'...")
    model = load_model(str(instance_path))

    print("\n--- Model Summary ---")
    print(f"Number of nodes: {model.num_nodes} (including depot)")
    print(f"Vehicle capacity (Q): {model.capacity}")
    print(f"Number of vehicles (K): {model.vehicles}")
    print(f"Time limit per route (T_max): {model.t_max}")
    print(f"Enforce mandatory: {enforce_mandatory}")

    solver = Solver(model, seed=4)
    final_solution = solver.solve_mandatory()

    # Write solution to file
    write_solution_to_file(final_solution, str(solution_path))
    
    # Validate Solution
    if solution_path:
        if not os.path.exists(solution_path):
            print(f"Error: Solution file '{solution_path}' does not exist.")
            return

        print(f"\n--- Validating solution from '{solution_path}' ---")
        routes = parse_solution_file(str(solution_path))

        print("\nRoutes Proposed:")
        for i, route in enumerate(routes):
            print(f"Route {i}: {route}")

        valid, report = validate_solution(model, routes, enforce_mandatory=enforce_mandatory)

        if valid:
            print("\n✅ Solution is VALID.")
            print(f"🏆 Total Profit Collected: {report['total_profit']}")
            print("\nRoute Details:")
            for i, (load, cost, profit) in enumerate(zip(report['route_loads'], report['route_costs'], report['route_profits'])):
                print(f"Route {i} -> Load = {load}/{model.capacity}, Time = {cost:.2f}/{model.t_max}, Profit = {profit}")
        else:
            print("\n❌ Solution is INVALID.")
            print("Errors Found:")
            for error in report['errors']:
                print(f" - {error}")

        plot_ctop_solution(model, routes)


if __name__ == "__main__":
    # Τα ονόματα των αρχείων όπως βρίσκονται στον εξωτερικό φάκελο
    main("ctop_main_instance.txt", "solution_mandatory.txt", True)