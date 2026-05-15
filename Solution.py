from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class Route:
    # Sequence of node IDs (always starts and ends with depot = 0)
    nodes: List[int] = field(default_factory=lambda: [0, 0])

    # Total demand served by this route
    load: int = 0

    # Total travel time of this route
    time: float = 0.0

    # Total collected profit
    profit: int = 0


@dataclass
class Solution:
    routes: List[Route]

    visited: Set[int] = field(default_factory=set)

    total_profit: int = 0
    total_time: float = 0.0
    total_load: int = 0


# from dataclasses import dataclass, field
# from typing import List
# @dataclass
# class Route:
#     # Sequence of node IDs (always starts and ends with depot = 0)
#     nodes: List[int] = field(default_factory=lambda: [0, 0])

#     # Total demand served by this route
#     load: int = 0

#     # Total travel time of this route
#     time: float = 0.0

#     # Total collected profit
#     profit: int = 0

# @dataclass
# class Solution:
#     def __init__(self, model):
#         self.model = model
#         self.routes = [[0, 0] for _ in range(model.vehicles)] # Initialize routes with depot at start and end
#         self.route_loads = [0] * model.vehicles
#         self.route_costs = [0.0] * model.vehicles
#         self.route_profits = [0] * model.vehicles
#         self.total_profit = 0
#         self.total_load = 0
#         self.total_cost = 0
        

#     # This method calculates the load, cost, and profit of a (one) given route
#     def calculate_route_metrics(self, route):
#         load = sum(self.model.nodes[node_id].demand for node_id in route)
#         cost = sum(self.model.cost_matrix[route[i]][route[i + 1]] for i in range(len(route) - 1))
#         profit = sum(self.model.nodes[node_id].profit for node_id in route)
#         return load, cost, profit
    
#     # This method calculates the total load, cost, and profit of the entire solution by summing up the metrics of all routes
#     def calculate_total_metrics(self):
#         self.total_load = sum(self.route_loads)
#         self.total_cost = sum(self.route_costs)
#         self.total_profit = sum(self.route_profits)

#     # This method updates the load, cost, and profit for each route and then updates the total metrics for the entire solution
#     def update_all_metrics(self):
#         for i, route in enumerate(self.routes):
#             load, cost, profit = self.calculate_route_metrics(route)
#             self.route_loads[i] = load
#             self.route_costs[i] = cost
#             self.route_profits[i] = profit
#         self.calculate_total_metrics()

#     # This method checks if the solution is valid based on the constraints of the problem
#     # Enforce mandatory nodes if enforce_mandatory is True, otherwise only check capacity and time constraints
#     def is_valid(self, enforce_mandatory=True):
#         visited = set()
#         for route in self.routes:
#             if not route:
#                 continue
#             if route[0] != 0 or route[-1] != 0:
#                 return False, "Each route must start and end at the depot (node 0)."
#             load, cost, profit = self.calculate_route_metrics(route)
#             if load > self.model.capacity:
#                 return False, f"Route {route} exceeds vehicle capacity."
#             if cost > self.model.t_max:
#                 return False, f"Route {route} exceeds time limit."
#             visited.update(route)

#         if enforce_mandatory:
#             for node in self.model.nodes:
#                 if node.isMandatory and node.id not in visited:
#                     return False, f"Mandatory node {node.id} is not visited."

#         return True, "Solution is valid."