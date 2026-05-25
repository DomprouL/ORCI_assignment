import os
import sys
import io
from pathlib import Path

from Parser import load_model
from SolutionValidator import validate_solution
from SolutionPlotter import plot_ctop_solution

from Solver import Solver
import Helpers as Helpers

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# Main για τους κόμβους "no mandatory" — φορτώνει το μοντέλο, τρέχει τον Solver
# γράφει το αποτέλεσμα σε αρχείο, το επικυρώνει και το σχεδιάζει.


def main(instance_file, solution_file, enforce_mandatory=False):
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

    # Αρχικοποίηση και εκτέλεση του Solver
    solver = Solver(model, seed=23)
    final_solution = solver.solve_no_mandatory()

    # Αποθήκευση λύσης
    Helpers.write_solution_to_file(final_solution, str(solution_path))
    routes_for_analysis = [route.nodes for route in final_solution.routes]

    if os.path.exists(solution_path):
        print(f"\n--- Validating solution from '{solution_path}' ---")
        valid, report = validate_solution(model, routes_for_analysis, enforce_mandatory=enforce_mandatory)

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

        plot_ctop_solution(model, routes_for_analysis)

if __name__ == "__main__":
    main("ctop_main_instance.txt", "solution_no_mandatory.txt")