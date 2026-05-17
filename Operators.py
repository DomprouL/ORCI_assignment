#swap in the same route
# def swap_intra_route(route):
#     new_route = route.copy()
#     best_cost = float('inf')
#     best_route = new_route.copy()
#     if len(new_route) <= 3:  # Not enough nodes to swap (excluding depot)
#         return False

#     for i in range(1, len(new_route) - 2):
#         for j in range(i + 1, len(new_route) - 1):
            
#             # Swap nodes at positions i and j
#             new_route[i], new_route[j] = new_route[j], new_route[i]
#             new_route.update_all_metrics()  # Update metrics after swap
#             if new_route.total_cost < best_cost:
#                 best_cost = new_route.total_cost
#                 best_route = new_route.copy()
#             # Swap back to original positions for next iteration
#             new_route[i], new_route[j] = new_route[j], new_route[i]
#             new_route.update_all_metrics()  # Update metrics after swap back
    
#     return best_route


import copy


def get_route_cost(route, model):
    """Βοηθητική συνάρτηση: Υπολογίζει το χρόνο μιας λίστας κόμβων."""
    cost = 0
    for i in range(len(route) - 1):
        cost += model.cost_matrix[route[i]][route[i+1]]
    return cost

def swap_intra_route(route, model):
    best_route = route[:]
    current_best_cost = get_route_cost(route, model)
    improved = False

    # Ξεκινάμε από το 1 και τελειώνουμε στο len-2 για να ΜΗΝ πειράξουμε τα Depot (0)
    for i in range(1, len(route) - 1):
        for j in range(i + 1, len(route) - 1):
            temp_route = route[:]
            temp_route[i], temp_route[j] = temp_route[j], temp_route[i]
            
            new_cost = get_route_cost(temp_route, model)
            if new_cost < current_best_cost:
                current_best_cost = new_cost
                best_route = temp_route[:]
                improved = True
    
    return best_route, improved

def swap_all_intra_route(routes, model):
    new_routes = []
    for route in routes:
        swapped_route, improved = swap_intra_route(route, model)
        if improved:
            new_routes.append(swapped_route)
        else:
            new_routes.append(route)  # No swap possible, keep original
    return new_routes


def apply_intra_route_swap(solution, model):
    new_solution = copy.deepcopy(solution)
    new_solution.routes = swap_all_intra_route(new_solution.routes, model)
    new_solution.update_all_metrics()
    return new_solution



def apply_inter_route_swap(solution, model):
    new_solution = copy.deepcopy(solution)
    improved = False
    for i in range(len(new_solution.routes)):
        for j in range(i + 1, len(new_solution.routes)):
            route1 = new_solution.routes[i]
            route2 = new_solution.routes[j]
            load1 = sum(model.nodes[n].demand for n in route1)
            load2 = sum(model.nodes[n].demand for n in route2)
            cost1 = get_route_cost(route1, model)
            cost2 = get_route_cost(route2, model)
            for k in range(1, len(route1) - 1):
                for l in range(1, len(route2) - 1):
                    # Swap nodes
                    temp_route1 = route1[:]
                    temp_route2 = route2[:]
                    temp_route1[k], temp_route2[l] = temp_route2[l], temp_route1[k]
                    new_load1 = load1 - model.nodes[route1[k]].demand + model.nodes[route2[l]].demand
                    new_load2 = load2 - model.nodes[route2[l]].demand + model.nodes[route1[k]].demand
                    if new_load1 > model.capacity or new_load2 > model.capacity:
                        continue
                    new_cost1 = get_route_cost(temp_route1, model)
                    new_cost2 = get_route_cost(temp_route2, model)
                    if new_cost1 > model.t_max or new_cost2 > model.t_max:
                        continue
                    if new_cost1 + new_cost2 < cost1 + cost2:
                        # Accept the swap
                        new_solution.routes[i] = temp_route1
                        new_solution.routes[j] = temp_route2
                        new_solution.update_all_metrics()
                        improved = True
                        break
                if improved:
                    break
            if improved:
                break
        if improved:
            break
    return new_solution
    

# def two_opt(solution, model):
#     # Implement the 2-opt algorithm for route improvement
#     new_solution = solution.copy()
#     for route in new_solution.routes:
#         if len(route) <= 3:  # Not enough nodes to perform 2-opt (excluding depot)
#             continue
#         best_cost = float('inf')
#         best_route = route.copy()
#         for i in range(1, len(route) - 2):
#             for j in range(i + 2, len(route) - 1):
#                 # Perform 2-opt swap by reversing the segment between i and j
#                 new_route = route[:i] + route[i:j][::-1] + route[j:]
#                 new_route.update_all_metrics()  # Update metrics after swap
#                 if new_route.total_cost < best_cost:
#                     best_cost = new_route.total_cost
#                     best_route = new_route.copy()
#         route[:] = best_route[:]  # Update the original route with the best found
#     new_solution.update_all_metrics()  # Update metrics after all routes are processed
#     return new_solution


def get_route_cost(route, model):
    """Βοηθητική συνάρτηση για τον υπολογισμό του χρόνου μιας λίστας κόμβων."""
    cost = 0
    for i in range(len(route) - 1):
        cost += model.cost_matrix[route[i]][route[i+1]]
    return cost

def two_opt(solution, model):
    # Δημιουργούμε ένα βαθύ αντίγραφο για να μην επηρεάσουμε την αρχική λύση
    import copy
    new_solution = copy.deepcopy(solution)
    
    for r_idx, route in enumerate(new_solution.routes):
        if len(route) <= 4:  # Χρειαζόμαστε τουλάχιστον 4 κόμβους (π.χ. [0, A, B, 0])
            continue
            
        improved = True
        while improved:
            improved = False
            best_cost = get_route_cost(route, model)
            
            # i: το σημείο πρώτης κοπής, j: το σημείο δεύτερης κοπής
            for i in range(1, len(route) - 2):
                for j in range(i + 1, len(route) - 1):
                    # Αντιστροφή του τμήματος μεταξύ i και j
                    # Το [i:j+1][::-1] αντιστρέφει το κομμάτι της διαδρομής
                    new_route = route[:i] + route[i:j+1][::-1] + route[j+1:]
                    
                    new_cost = get_route_cost(new_route, model)
                    
                    if new_cost < best_cost:
                        route = new_route[:]
                        best_cost = new_cost
                        improved = True
            
            # Ενημέρωση της διαδρομής στο αντικείμενο solution
            new_solution.routes[r_idx] = route

    # Στο τέλος ενημερώνουμε όλα τα metrics του αντικειμένου Solution
    new_solution.calculate_total_metrics() 
    return new_solution


def node_exchange(solution, model):
    # αντικαθιστούμε ένα κόμβο σε μια διαδρομή με ένα κόμβο που δεν έχει εξυπηρετηθεί
    unvisited = set(range(1, model.num_nodes)) - solution.visited

    for route in solution.routes:
        for i in range(1, len(route.nodes) - 1):
            node_i = route.nodes[i]
            A = route.nodes[i - 1]
            B = route.nodes[i + 1]

            for j in unvisited:
                new_time = route.time - model.cost_matrix[A][node_i] - model.cost_matrix[node_i][B] + model.cost_matrix[j][B] + model.cost_matrix[A][j]
                new_load = route.load - model.nodes[node_i].demand + model.nodes[j].demand
                new_profit = route.profit - model.nodes[node_i].profit + model.nodes[j].profit

                if new_time <= model.t_max and new_load <= model.capacity and new_profit > route.profit:
                    route.nodes[i] = j
                    route.time = new_time
                    route.load = new_load
                    route.profit = new_profit

                    solution.visited.remove(node_i)
                    solution.visited.add(j)
                    unvisited.remove(j)
                    unvisited.add(node_i)
                    break
    return solution