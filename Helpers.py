import heapq
from dataclasses import dataclass, field
from typing import List


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

# I use a min-heap to identify the k nearest neighbors for each node, where k is a user-defined parameter.
# The neighbor IDs are stored in a list (per node) in sorted order, allowing efficient access based on proximity.
# Additionally, I store the same neighbor IDs in a set (per node) to enable faster lookup and set operations.
# A min-heap is used due to its favorable time complexity and efficiency compared to alternative approaches.
def build_nearest_neighbors_heap(model, k=50):

    neighbors_list_array = []
    neighbors_set_array = []

    for i in range(model.num_nodes):

        heap = []

        for j in range(model.num_nodes):
            if i == j:
                continue

            cost_ij = model.cost_matrix[i][j]

            if len(heap) < k:
                heapq.heappush(heap, (-cost_ij, j))

            else:
                current_max_cost = -heap[0][0]

                if cost_ij < current_max_cost:
                    heapq.heapreplace(heap, (-cost_ij, j))

        nearest_neighbors = [node_id for neg_cost, node_id in heap]
        nearest_neighbors.sort(key=lambda node_id: model.cost_matrix[i][node_id])

        nearest_neighbors_set = set(nearest_neighbors)

        neighbors_list_array.append(nearest_neighbors)
        neighbors_set_array.append(nearest_neighbors_set)

    return neighbors_list_array, neighbors_set_array

#Computes the average distance of all node pairs in the cost matrix, excluding the main diagonal (ignoring seld distances)
def compute_average_distance(model):

    count = 0
    sum_dist = 0 
    for i in range (model.num_nodes):
        for j in range (model.num_nodes):
            if i != j:
                sum_dist += model.cost_matrix[i][j]
                count += 1
    avg_distance = sum_dist/count
    return avg_distance

# Computes the average demand across all nodes except depot.
def compute_average_demand(model):

    count = 0 
    sum_dem = 0

    for i in range(1, model.num_nodes):  
        sum_dem += model.nodes[i].demand
        count += 1 

    avg_demand = sum_dem / count
    return avg_demand

# Computes the extra travel time caused by inserting node j between nodes a and b.
def calculate_added_time(model, a, j, b):

    added_time = model.cost_matrix[a][j] + model.cost_matrix[j][b] - model.cost_matrix[a][b]

    return added_time

 # Checks if node j can be inserted into the route without violating:
    # 1. the uniqueness constraint,
    # 2. the vehicle capacity constraint,
    # 3. the maximum route time constraint.
def is_feasible_insertion(model, route, j, added_time, visited):

    if j in visited:
        return False

    if route.load + model.nodes[j].demand > model.capacity:
        return False

    if route.time + added_time > model.t_max:
        return False

    return True

# Inserts node j into the route at the given position. Then updates the route's load, time, and profit.
def insert_node(model, route, j, position, added_time):

    route.nodes.insert(position, j)
    route.load += model.nodes[j].demand
    route.time += added_time
    route.profit += model.nodes[j].profit

#Finds the best feasible insertion in a route. 
def find_best_insertion_for_route(model, route, visited, avg_demand, avg_distance, neighbors_set_array):
    best_score = -1
    best_node = None
    best_position = None
    best_added_time = None

    for i in range(len(route.nodes) - 1):
        a = route.nodes[i]
        b = route.nodes[i + 1]

        set_a = neighbors_set_array[a]
        set_b = neighbors_set_array[b]

        candidates = set_a.union(set_b)

        for j in candidates:

            if j in visited:
                continue

            if j == 0:
                continue

            added_time = calculate_added_time(model, a, j, b)

            if not is_feasible_insertion(model, route, j, added_time, visited):
                continue

            demand_norm = model.nodes[j].demand / avg_demand
            time_norm = added_time / avg_distance

            alpha = 0.6

            denominator = alpha * demand_norm + (1 - alpha)* time_norm

            if denominator <= 0:
                continue
            
            score = model.nodes[j].profit / (denominator)

            if model.nodes[j].demand == 1:
                score += 20

            if score > best_score:
                best_score = score
                best_node = j
                best_position = i + 1
                best_added_time = added_time

    return best_node, best_position, best_added_time, best_score

# Finds the best feasible insertion among all available routes. 
# It calls find_best_insertion_for_route for each route and keeps the insertion with the highest score.
def find_best_global_insertion(model, routes, visited, avg_demand, avg_distance, neighbors_set_array):

    best_route = None
    best_node = None
    best_position = None
    best_added_time = None
    best_score = -1

    for route in routes:
        node, position, added_time, score = find_best_insertion_for_route(
            model, route, visited, avg_demand, avg_distance, neighbors_set_array
        )

        if node is not None and score > best_score:
            best_route = route
            best_node = node
            best_position = position
            best_added_time = added_time
            best_score = score

    return best_route, best_node, best_position, best_added_time, best_score

# # Starts with one route.
# # Opens a new empty route only when all existing routes have at least one customer.
# # Stops opening new routes when the number of routes reaches the number of vehicles.
def construct_initial_solution(model, avg_demand, avg_distance, neighbors_set_array):

    routes = [Route()]
    visited = set()

    while True:

        all_routes_have_customer = all(len(route.nodes) > 2 for route in routes)

        if all_routes_have_customer and len(routes) < model.vehicles:
            routes.append(Route())

        best_route, node, position, added_time, score = find_best_global_insertion(
            model, routes, visited, avg_demand, avg_distance, neighbors_set_array
        )

        if node is None:
            break

        insert_node(model, best_route, node, position, added_time)
        visited.add(node)

    return routes, visited

# Computes the total profit, total travel time, and number of used routes.
def compute_solution_totals(routes):

    total_profit = 0
    total_time = 0.0
    used_routes = 0

    for route in routes:
        total_profit += route.profit
        total_time += route.time

        if len(route.nodes) > 2:
            used_routes += 1

    return total_profit, total_time, used_routes