from Operators import apply_inter_route_swap, apply_inter_route_swap, apply_intra_route_swap, swap_intra_route, two_opt
import Solution
import Helpers
class Solver:
    def __init__(self, model, seed):
        self.model = model
        self.seed = seed 
    
    def solve_greedy(self, enforce_mandatory=True):
        # Implement a greedy heuristic to construct an initial solution
        #uses minimum cost insertion heuristic to construct the initial solution
        # The code selection in based oh the utilization og the node
        initial_solution = Solution.Solution(self.model)
        utilization = Helpers.calculate_utilization(self.model.nodes, enforce_mandatory)
        #unvisited = set(range(1, self.model.num_nodes))  # Exclude depot
        total_load = initial_solution.total_load
        
        while total_load < self.model.capacity and utilization:
            node_id = utilization.pop(0)
            node = self.model.nodes[node_id]
            selected_possition = None
            selected_route = None
            minimum_additional_cost = float('inf')
            for route in initial_solution.routes:
                route_load = sum(self.model.nodes[n].demand for n in route)
                for i in range(1, len(route)):
                    prev_node = route[i - 1]
                    next_node = route[i]
                    additional_cost = self.model.cost_matrix[prev_node][node_id] + self.model.cost_matrix[node_id][next_node] - self.model.cost_matrix[prev_node][next_node]
                    if route_load + node.demand <= self.model.capacity and initial_solution.route_costs[initial_solution.routes.index(route)] + additional_cost <= self.model.t_max:
                        if additional_cost < minimum_additional_cost:
                            minimum_additional_cost = additional_cost
                            selected_route = route
                            selected_possition = i
            if selected_route is not None:
                selected_route.insert(selected_possition, node_id)
                initial_solution.update_all_metrics()
        
        

           
        return initial_solution

    # def local_search(self, solution):
    #     improved = True
    #     while improved:
    #         old_profit = solution.total_profit
    #         old_cost = solution.total_cost
            
    #         # Εφαρμογή βελτιώσεων
    #         solution = apply_intra_route_swap(solution, self.model)
    #         solution = two_opt(solution, self.model)
    #         solution = apply_inter_route_swap(solution, self.model)
            
    #         # Έλεγχος αν υπήρξε πραγματική βελτίωση (σε κέρδος ή χρόνο)
    #         solution.update_all_metrics()
    #         if solution.total_profit > old_profit or (solution.total_profit == old_profit and solution.total_cost < old_cost):
    #             improved = True
    #         else:
    #             improved = False
    #     return solution
        
            
    def local_search(self, solution):
        improved = True
        print("Starting local search...")
        while improved:
            old_profit = solution.total_profit
            old_cost = solution.total_cost
            
            # Εφαρμογή βελτιώσεων
            solution = apply_intra_route_swap(solution, self.model)
            solution = two_opt(solution, self.model)
            solution = apply_inter_route_swap(solution, self.model)
            
            # Έλεγχος αν υπήρξε πραγματική βελτίωση (σε κέρδος ή χρόνο)
            solution.update_all_metrics()
            if solution.total_profit > old_profit or (solution.total_profit == old_profit and solution.total_cost < old_cost):
                improved = True
            else:
                improved = False
        return solution


        

    def alns(self, solution, enforce_mandatory=True):
        # Implement the ALNS metaheuristic to further improve the solution
        pass

    

    def solve(self, enforce_mandatory=True):
        # Main method to solve the problem
        initial_solution = self.solve_greedy(enforce_mandatory)
        improved_solution = self.local_search(initial_solution)

        return improved_solution
        # return initial_solution
        