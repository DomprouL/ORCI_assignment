import copy
import random
from Solution import Route, Solution
import Helpers as Helpers
from Capacity_Repair import (
    warm_start_remove_insert_loop,
    repair_solution_with_insertions,
    capacity_destroy_repair_search_sa
)
from Time_Operators import time_vnd



class Solver: 
    """Solver για μη-υποχρεωτικούς κόμβους. Επιστρέφει Solution."""
    def __init__(self, model, seed):
        self.model = model
        self.seed = seed
        
        random.seed(seed)

        self.avg_demand = Helpers.compute_average_demand(model)
        self.avg_distance = Helpers.compute_average_distance(model)

        (
            self.neighbors_list_array,
            self.neighbors_set_array
        ) = Helpers.build_nearest_neighbors_heap(model)

    def insert_node(self, route, node, position, added_time):
        route.nodes.insert(position, node)
        route.load += self.model.nodes[node].demand
        route.time += added_time
        route.profit += self.model.nodes[node].profit

    def find_best_insertion_for_route(self, route, visited):
        best_score = -1
        best_node = None
        best_position = None
        best_added_time = None

        for i in range(len(route.nodes) - 1):
            a = route.nodes[i]
            b = route.nodes[i + 1]

            set_a = self.neighbors_set_array[a]
            set_b = self.neighbors_set_array[b]
            candidates = set_a.union(set_b)

            for j in candidates:
                if j in visited or j == 0:
                    continue

                added_time = Helpers.calculate_added_time(self.model, a, j, b)
                if not Helpers.is_feasible_insertion(self.model, route, j, added_time, visited):
                    continue

                demand_norm = self.model.nodes[j].demand / self.avg_demand
                time_norm = added_time / self.avg_distance

                alpha = 0.6
                denominator = alpha * demand_norm + (1 - alpha) * time_norm

                if denominator <= 0:
                    continue
                    
                score = self.model.nodes[j].profit / denominator
                if self.model.nodes[j].demand == 1:
                    score += 20

                if score > best_score:
                    best_score = score
                    best_node = j
                    best_position = i + 1
                    best_added_time = added_time

        return best_node, best_position, best_added_time, best_score

    def find_best_global_insertion(self, routes, visited, top_k=5):
        candidates = []
        for route in routes:
            node, position, added_time, score = self.find_best_insertion_for_route(route, visited)
            if node is not None:
                candidates.append((score, route, node, position, added_time))

        if not candidates:
            return None, None, None, None, -1

        candidates.sort(reverse=True, key=lambda x: x[0])
        restricted_candidates = candidates[:top_k]
        score, route, node, position, added_time = random.choice(restricted_candidates)

        return route, node, position, added_time, score

    def construct_initial_solution(self, top_k=5):
        routes = [Route()]
        visited = set()

        while True:
            all_routes_have_customer = all(len(route.nodes) > 2 for route in routes)
            if all_routes_have_customer and len(routes) < self.model.vehicles:
                routes.append(Route())

            best_route, node, position, added_time, score = self.find_best_global_insertion(routes, visited, top_k)
            if node is None:
                break

            self.insert_node(best_route, node, position, added_time)
            visited.add(node)

        return routes, visited

    def multi_restart_initial_solution(self, restarts=30, top_k=5):
        best_routes = []
        best_visited = set()
        best_profit = -1
        best_time = float("inf")


        for iteration in range(1, restarts + 1):
            routes, visited = self.construct_initial_solution(top_k=top_k)
            
            # VND αμέσως μετά την κατασκευή
            time_vnd(self.model, routes, self.neighbors_set_array)
            
            current_profit = sum(r.profit for r in routes)
            current_time = sum(r.time for r in routes)

            if current_profit > best_profit or (current_profit == best_profit and current_time < best_time):
                best_routes = copy.deepcopy(routes)
                best_visited = copy.deepcopy(visited)
                best_profit = current_profit
                best_time = current_time


        return best_routes, best_visited

    def solve_no_mandatory(self):
        # Κατασκευή αρχικής λύσης
        routes, visited = self.multi_restart_initial_solution(restarts=30, top_k=5)

        # Βελτίωση με warm-start
        warm_start_remove_insert_loop(
            self.model, routes, visited, self.avg_demand, self.avg_distance, self.neighbors_set_array,
            solver=self, top_k=1, protect_mandatory=False
        )

        # Destroy-repair με SA
        routes, visited, best_profit, best_time = capacity_destroy_repair_search_sa(
            self.model, routes, visited, self.avg_demand, self.avg_distance, self.neighbors_set_array,
            iterations=100, remove_min=1, remove_max=7, bad_pool_size=30,
            insertion_top_k=3, seed=4, protect_mandatory=False, use_vnd=False,
            start_temperature=80.0, end_temperature=1.0, solver=self
        )

        # Τελική βελτίωση (VND + insertions)
        for _ in range(5):
            before_profit = sum(r.profit for r in routes)
            time_vnd(self.model, routes, self.neighbors_set_array)
            repair_solution_with_insertions(
                self.model, routes, visited, self.avg_demand, self.avg_distance, self.neighbors_set_array,
                solver=self, top_k=1
            )
            if sum(r.profit for r in routes) == before_profit:
                break

        return Solution(routes=routes, visited=visited)