import random
import Helpers
import copy
from ALNS import ALNS
from ALNS_mandatory import ALNS as ALNS_mandatory

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


    def remove_node(self, route, position):
        node = route.nodes[position]
        a = route.nodes[position - 1]
        b = route.nodes[position + 1]

        removed_time = (
            self.model.cost_matrix[a][node]
            + self.model.cost_matrix[node][b]
            - self.model.cost_matrix[a][b]
        )

        route.nodes.pop(position)
        route.load -= self.model.nodes[node].demand
        route.time -= removed_time
        route.profit -= self.model.nodes[node].profit

        return node

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
                    
                score = self.model.nodes[j].profit / (denominator)

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
        top_k=3
    ):

        best_solution = None

        best_profit = -1
        best_time = float("inf")

        print("\niteration current_solution best_solution")

        for iteration in range(1, restarts + 1):

            solution = self.construct_initial_solution(
                top_k=top_k
            )

            current_profit = solution.total_profit
            current_time = solution.total_time

            if (
                current_profit > best_profit
                or (
                    current_profit == best_profit
                    and current_time < best_time
                )
            ):

                best_solution = solution

                best_profit = current_profit
                best_time = current_time

            print(
                iteration,
                current_profit,
                best_profit,
                flush=True
            )

        return best_solution

    #def solve_greedy(self, enforce_mandatory=True):

        # solution = Solution(self.model)
        # print(type(solution))
        # print(type(solution.routes))
        # utilization = Helpers.calculate_utilization(
        #     self.model.nodes,
        #     enforce_mandatory
        # )

        # while utilization:

        #     node_id = utilization.pop(0)
        #     node = self.model.nodes[node_id]

        #     best_route = None
        #     best_pos = None
        #     best_cost = float("inf")

        #     for route in solution.routes:

        #         for i in range(1, len(route.nodes)):

        #             prev_node = route.nodes[i - 1]
        #             next_node = route.nodes[i]

        #             additional_cost = (
        #                 self.model.cost_matrix[prev_node][node_id]
        #                 + self.model.cost_matrix[node_id][next_node]
        #                 - self.model.cost_matrix[prev_node][next_node]
        #             )

        #             if (
        #                 route.load + node.demand <= self.model.capacity
        #                 and route.time + additional_cost <= self.model.t_max
        #             ):

        #                 if additional_cost < best_cost:
        #                     best_cost = additional_cost
        #                     best_route = route
        #                     best_pos = i

        #     if best_route is not None:

        #         self.insert_node(
        #             best_route,
        #             node_id,
        #             best_pos,
        #             best_cost
        #         )

        # return solution



    def solve_greedy(self, enforce_mandatory=True):

        routes = [Route() for _ in range(self.model.vehicles)]
        visited = set()

        utilization = Helpers.calculate_utilization(
            self.model.nodes,
            enforce_mandatory
        )

        for node_id in utilization:

            node = self.model.nodes[node_id]

            best_route = None
            best_pos = None
            best_cost = float("inf")

            for route in routes:

                for i in range(1, len(route.nodes)):

                    a = route.nodes[i - 1]
                    b = route.nodes[i]

                    delta_cost = (
                        self.model.cost_matrix[a][node_id]
                        + self.model.cost_matrix[node_id][b]
                        - self.model.cost_matrix[a][b]
                    )

                    new_load = route.load + node.demand
                    new_time = route.time + delta_cost

                    if new_load > self.model.capacity:
                        continue
                    if new_time > self.model.t_max:
                        continue

                    if delta_cost < best_cost:
                        best_cost = delta_cost
                        best_route = route
                        best_pos = i

            if best_route is not None:
                best_route.nodes.insert(best_pos, node_id)
                best_route.load += node.demand
                best_route.time += best_cost
                best_route.profit += node.profit
                visited.add(node_id)

        sol = Solution(routes=routes, visited=visited)

        sol.total_profit = sum(r.profit for r in routes)
        sol.total_load = sum(r.load for r in routes)
        sol.total_time = sum(r.time for r in routes)

        return sol

    # def solve_mandatory(self, restarts=20, top_k=3):

    #     best_solution = None
    #     best_profit = -1
    #     best_time = float("inf")

    #     for _ in range(restarts):

    #         sol = self.construct_initial_solution(top_k=top_k)

    #         # VALIDITY FILTER (mandatory must be satisfied)
    #         visited = sol.visited

    #         all_mandatory_ok = all(
    #             (not n.isMandatory) or (n.id in visited)
    #             for n in self.model.nodes
    #         )

    #         if not all_mandatory_ok:
    #             continue

    #         if (sol.total_profit > best_profit or
    #             (sol.total_profit == best_profit and sol.total_time < best_time)):

    #             best_solution = sol
    #             best_profit = sol.total_profit
    #             best_time = sol.total_time

    #     return best_solution

    def solve_mandatory(self):

        initial_solution = self.solve_greedy(enforce_mandatory=True)

        # (optional) sanity update
        initial_solution.total_profit = sum(r.profit for r in initial_solution.routes)
        initial_solution.total_load = sum(r.load for r in initial_solution.routes)
        initial_solution.total_time = sum(r.time for r in initial_solution.routes)

        alns = ALNS_mandatory(self.model,self.seed)
        #solution = alns.run(initial_solution, interations=500)
        solution = local_search(self.model, initial_solution)
        return solution
        return initial_solution


    def solve_no_mandatory(self):
        initial_solution = self.multi_restart_initial_solution(restarts=3, top_k=5)

        alns = ALNS(self.model,self.seed)
        solution = alns.run(initial_solution, interations=500)
        return solution

