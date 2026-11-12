"""Generate and validate the two CTOP solutions."""
import argparse
from pathlib import Path
from time import perf_counter

from ctop.Parser import load_model
from ctop.SolutionPlotter import infer_coordinates, plot_ctop_solution
from ctop.SolutionValidator import parse_solution_file, validate_solution
from mandatory.Solver import Solver as MandatorySolver
from no_mandatory.Solver import solve_standard

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    model = load_model(ROOT / "data" / "ctop_main_instance.txt")
    coordinates = infer_coordinates(model)
    for scenario, label, solve, mandatory in (
        ("mandatory", "Mandatory CTOP", lambda: MandatorySolver(model, seed=4).solve_mandatory().routes, True),
        ("no_mandatory", "Standard CTOP", lambda: solve_standard(model), False),
    ):
        start = perf_counter()
        solution_routes = solve()
        elapsed = perf_counter() - start
        routes = [route.nodes for route in solution_routes if len(route.nodes) > 2]
        valid, report = validate_solution(model, routes, enforce_mandatory=mandatory)
        if not valid:
            raise RuntimeError(f"{label}: {'; '.join(report['errors'])}")

        solution_path = args.output_dir / f"solution_{scenario}.txt"
        solution_path.write_text(
            "".join(" ".join(map(str, route)) + "\n" for route in routes),
            encoding="utf-8",
        )
        saved_routes = parse_solution_file(solution_path)
        plot_ctop_solution(
            model, saved_routes, coordinates, label, mandatory,
            args.output_dir / f"routes_{scenario}.png",
        )
        print(
            f"{label}: valid | profit {report['total_profit']:,} | "
            f"route time {report['total_cost']:,.1f} | fleet {len(routes)}/{model.vehicles} | "
            f"solver {elapsed:.2f}s",
            flush=True,
        )


if __name__ == "__main__":
    main()
