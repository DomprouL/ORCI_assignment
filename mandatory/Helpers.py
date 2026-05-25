import heapq
from pathlib import Path

def write_solution_to_file(solution, filename):
    current_folder = Path(__file__).resolve().parent
    output_path = current_folder / filename
    
    with open(output_path, "w", encoding="utf-8") as f:
        for route in solution.routes:
            if len(route.nodes) > 2:
                f.write(" ".join(map(str, route.nodes)) + "\n")

# Κατασκευή λίστας k κοντινότερων γειτόνων για κάθε κόμβο.
# Επιστρέφεται λίστα και σύνολο για γρήγορες αναζητήσεις.
def build_nearest_neighbors_heap(model, k=75):

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




def cluster_mandatory_nodes(model, n_vehicles):
    # ομαδοποιούμε τα mandatory nodes που είναι κοντά μεταξύ τους για να τα βάλουμε σε ένα φορτηγό
    mandatory = [n.id for n in model.nodes if n.isMandatory]
    
    # Διάλεγουμε 5 κέντρα
    centers = [mandatory[0]]
    while len(centers) < n_vehicles:
        best = None
        best_dist = -1
        for node in mandatory:
            if node in centers:
                continue
            min_dist = min(model.cost_matrix[node][c] for c in centers)
            if min_dist > best_dist:
                best_dist = min_dist
                best = node
        centers.append(best)
    
    clusters = [[] for _ in range(n_vehicles)]
    for node in mandatory:
        closest = min(range(n_vehicles), 
                     key=lambda k: model.cost_matrix[node][centers[k]])
        clusters[closest].append(node)
    
    return clusters
