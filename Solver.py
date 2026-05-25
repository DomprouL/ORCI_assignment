import random


import Helpers
import copy
from ALNS import ALNS
from ILS import ILS
from PathRelinking import EliteSet, path_relinking

from LocalSearch import local_search
from Solution import Route, Solution

class Solver: 
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


    #Finds the best feasible insertion in a route. 
    def find_best_insertion_for_route(self,route, visited):


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

                if j in visited:
                    continue

                if j == 0:
                    continue

                added_time = Helpers.calculate_added_time(self.model, a, j, b)

                if not Helpers.is_feasible_insertion(self.model, route, j, added_time, visited):
                    continue

                demand_norm = self.model.nodes[j].demand / self.avg_demand
                time_norm = added_time / self.avg_distance

                alpha = 0.6

                denominator = alpha * demand_norm + (1 - alpha)* time_norm

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

    def find_best_global_insertion(self,routes, visited, top_k=5
    ):
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

            all_routes_have_customer = all(
                len(route.nodes) > 2
                for route in routes
            )

            if (
                all_routes_have_customer
                and len(routes) < self.model.vehicles
            ):
                routes.append(Route())

            best_route, node, position, added_time, score = (
                self.find_best_global_insertion(
                    routes,
                    visited,
                    top_k
                )
            )

            if node is None:
                break

            self.insert_node(
                best_route,
                node,
                position,
                added_time
            )

            visited.add(node)

        solution = Solution(
            routes=routes,
            visited=visited
        )

        solution.total_profit = sum(r.profit for r in routes)
        solution.total_time = sum(r.time for r in routes)
        solution.total_load = sum(r.load for r in routes)

        return solution
    

    def multi_restart_initial_solution(
            self,
            restarts=100,
            top_k=3,
            enforce_mandatory=False
        ):
            """
            Παράγει μια ισχυρή αρχική λύση μέσω πολλαπλών restarts.
            Κρατάει τις κορυφαίες λύσεις στο Elite Set και εκτελεί Path Relinking 
            ανάμεσα στην τρέχουσα λύση και τις ήδη υπάρχουσες elite λύσεις.
            """
            best_solution = None
            best_profit = -1
            best_time = float("inf")

            print("\nIteration | Current Profit | Best Profit")
            print("-" * 40)

            for iteration in range(1, restarts + 1):
                # Κατασκευή αρχικής τυχαίας λύσης
                solution = self.construct_initial_solution(top_k=top_k)
                
                # local search 
                solution = local_search(self.model, solution, enforce_mandatory=enforce_mandatory)

                current_profit = solution.total_profit
                current_time = solution.total_time

                # Έλεγχος αν βρήκαμε νέα καθολικά καλύτερη λύση
                if (
                    current_profit > best_profit
                    or (
                        current_profit == best_profit
                        and current_time < best_time
                    )
                ):
                    best_solution = copy.deepcopy(solution)
                    best_profit = current_profit
                    best_time = current_time

                

            return best_solution



    def solve_mandatory_clustered(self):
        from Helpers import cluster_mandatory_nodes
        
        # Ομαδοποίηση mandatory
        clusters = cluster_mandatory_nodes(self.model, self.model.vehicles)
        
        routes = [Route() for _ in range(self.model.vehicles)]
        visited = set()
        
        # Κάθε όχημα παίρνει τους mandatory της ομάδας του
        for k, route in enumerate(routes):
            for node_id in clusters[k]:
                # καλύτερη θέση για τον συγκεκριμένο mandatory
                best_pos = 1
                best_time = float('inf')
                for i in range(1, len(route.nodes)):
                    a = route.nodes[i-1]
                    b = route.nodes[i]
                    delta = self.model.cost_matrix[a][node_id] + self.model.cost_matrix[node_id][b] - self.model.cost_matrix[a][b]
                    new_time = route.time + delta
                    if new_time <= self.model.t_max and route.load + self.model.nodes[node_id].demand <= self.model.capacity:
                        if delta < best_time:
                            best_time = delta
                            best_pos = i
                
                self.insert_node(route, node_id, best_pos, best_time)
                visited.add(node_id)
        
        # εισάγει τα μη mandatory με greedy τρόπο
        while True:
            best_route, node, position, added_time, score = self.find_best_global_insertion(routes, visited)
            if node is None:
                break
            self.insert_node(best_route, node, position, added_time)
            visited.add(node)
        
        solution = Solution(routes=routes, visited=visited)
        solution.total_profit = sum(r.profit for r in routes)
        solution.total_time = sum(r.time for r in routes)
        solution.total_load = sum(r.load for r in routes)
        
        return solution



    def solve_mandatory(self):
        solution = None
        best_profit = -1

        elite = EliteSet(self.model, max_size=5, enforce_mandatory=True)
        
        for i in range(10):
            candidate = self.solve_mandatory_clustered()
            

            
            elite.try_add(candidate)
            for elite_sol in elite.solutions:
                if elite_sol.total_profit == candidate.total_profit:
                    continue
                
                if candidate.total_profit > elite_sol.total_profit:
                    start, end = copy.deepcopy(candidate), copy.deepcopy(elite_sol)
                else:
                    start, end = copy.deepcopy(elite_sol), copy.deepcopy(candidate)
                # Εκτέλεση Path Relinking
                pr_sol = path_relinking(self.model, start, end, enforce_mandatory=True)
                

                pr_sol = local_search(self.model, pr_sol, enforce_mandatory=True)
                
                if pr_sol.total_profit > best_profit:
                    solution = pr_sol
                    best_profit = pr_sol.total_profit
                    
            if candidate.total_profit > best_profit:
                best_profit = candidate.total_profit
                solution = candidate

       

        #  Local search 
        solution = local_search(self.model, solution, enforce_mandatory=True)
        print(f"After Local Search: {solution.total_profit}")

        #  ILS        

        ils = ILS(self.model, seed=self.seed, enforce_mandatory=True)
        ils_sol = ils.run(solution, iterations=500)

        best_sol = local_search(self.model, ils_sol, enforce_mandatory=True)
        
        return best_sol


    def solve_no_mandatory(self):
        


        initial_sol = self.multi_restart_initial_solution( restarts=10, top_k=5)

        print(f"Αρχική λύση: {initial_sol.total_profit}")

        # Local Search για γρήγορη βελτίωση
        solution = local_search(self.model, initial_sol)
        print(f"Μετά Local Search: {solution.total_profit}")

        
    
        alns = ALNS(self.model, self.seed)
        alns_sol = alns.run(solution, iterations=500)
        print(f"After ALNS: {alns_sol.total_profit}")
        
        print(f"Μετά ALNS: {alns_sol.total_profit}")

       
        best_sol = copy.deepcopy(alns_sol)
        
        best_sol = local_search(self.model, best_sol)

        return best_sol


    def solve(self, enforce_mandatory=True):
        if enforce_mandatory:
            return self.solve_mandatory()
        else:
            return self.solve_no_mandatory()
        
    
