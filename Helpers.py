import heapq
from dataclasses import dataclass, field
from typing import List
import random

def write_solution_to_file(solution, filename):

    with open(filename, "w") as f:

        for route in solution.routes:

            if len(route.nodes) > 2:
                f.write(" ".join(map(str, route.nodes)) + "\n")

        

# I use a min-heap to identify the k nearest neighbors for each node, where k is a user-defined parameter.
# The neighbor IDs are stored in a list (per node) in sorted order, allowing efficient access based on proximity.
# Additionally, I store the same neighbor IDs in a set (per node) to enable faster lookup and set operations.
# A min-heap is used due to its favorable time complexity and efficiency compared to alternative approaches.
def build_nearest_neighbors_heap(model, k=80):

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



# Gets a list of nodes, Calculates the total utilization of each node (profit/demand) and returns a list of node IDs sorted by utilization in descending order
# If enforce_mandatory is True, mandatory nodes will be prioritized in the utilization list regardless of their profit/demand ratio
def calculate_utilization (nodes, enforce_mandatory=True):
    if enforce_mandatory:
        node_utilization = []
        mandatory_nodes = []
        optional_nodes = []
        for node in nodes:
            if node.demand > 0:
                utilization = node.profit / node.demand
                
                if node.isMandatory:
                    mandatory_nodes.append((node.id, utilization))
                else:
                    optional_nodes.append((node.id, utilization))
        

        # Sort mandatory nodes by profit/demand ratio
        mandatory_nodes_sorted = (node_id for node_id, _ in sorted(mandatory_nodes, key=lambda x: x[1], reverse=True))
        # Sort optional nodes by profit/demand ratio
        optional_nodes_sorted = (node_id for node_id, _ in sorted(optional_nodes, key=lambda x: x[1], reverse=True))

        # Combine mandatory and optional nodes, with mandatory nodes first
        sorted_nodes = list(mandatory_nodes_sorted) + list(optional_nodes_sorted)
    else:
        node_utilization = []
        for node in nodes:
            if node.demand > 0:
                node_utilization.append((node.id, node.profit / node.demand))
        sorted_nodes = [node_id for node_id, _ in sorted(node_utilization, key=lambda x: x[1], reverse=True)]
    # Return the sorted list of node IDs based on utilization
    return sorted_nodes