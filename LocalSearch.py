# # #swap in the same route
# # # def swap_intra_route(route):
# # #     new_route = route.copy()
# # #     best_cost = float('inf')
# # #     best_route = new_route.copy()
# # #     if len(new_route) <= 3:  # Not enough nodes to swap (excluding depot)
# # #         return False

# # #     for i in range(1, len(new_route) - 2):
# # #         for j in range(i + 1, len(new_route) - 1):
            
# # #             # Swap nodes at positions i and j
# # #             new_route[i], new_route[j] = new_route[j], new_route[i]
# # #             new_route.update_all_metrics()  # Update metrics after swap
# # #             if new_route.total_cost < best_cost:
# # #                 best_cost = new_route.total_cost
# # #                 best_route = new_route.copy()
# # #             # Swap back to original positions for next iteration
# # #             new_route[i], new_route[j] = new_route[j], new_route[i]
# # #             new_route.update_all_metrics()  # Update metrics after swap back
    
# # #     return best_route


# # import copy


# # def get_route_cost(route, model):
# #     """Βοηθητική συνάρτηση: Υπολογίζει το χρόνο μιας λίστας κόμβων."""
# #     cost = 0
# #     for i in range(len(route) - 1):
# #         cost += model.cost_matrix[route[i]][route[i+1]]
# #     return cost

# # def swap_intra_route(route, model):
# #     best_route = route[:]
# #     current_best_cost = get_route_cost(route, model)
# #     improved = False

# #     # Ξεκινάμε από το 1 και τελειώνουμε στο len-2 για να ΜΗΝ πειράξουμε τα Depot (0)
# #     for i in range(1, len(route) - 1):
# #         for j in range(i + 1, len(route) - 1):
# #             temp_route = route[:]
# #             temp_route[i], temp_route[j] = temp_route[j], temp_route[i]
            
# #             new_cost = get_route_cost(temp_route, model)
# #             if new_cost < current_best_cost:
# #                 current_best_cost = new_cost
# #                 best_route = temp_route[:]
# #                 improved = True
    
# #     return best_route, improved

# # def swap_all_intra_route(routes, model):
# #     new_routes = []
# #     for route in routes:
# #         swapped_route, improved = swap_intra_route(route, model)
# #         if improved:
# #             new_routes.append(swapped_route)
# #         else:
# #             new_routes.append(route)  # No swap possible, keep original
# #     return new_routes


# # def apply_intra_route_swap(solution, model):
# #     new_solution = copy.deepcopy(solution)
# #     new_solution.routes = swap_all_intra_route(new_solution.routes, model)
# #     new_solution.update_all_metrics()
# #     return new_solution



# # def apply_inter_route_swap(solution, model):
# #     new_solution = copy.deepcopy(solution)
# #     improved = False
# #     for i in range(len(new_solution.routes)):
# #         for j in range(i + 1, len(new_solution.routes)):
# #             route1 = new_solution.routes[i]
# #             route2 = new_solution.routes[j]
# #             load1 = sum(model.nodes[n].demand for n in route1)
# #             load2 = sum(model.nodes[n].demand for n in route2)
# #             cost1 = get_route_cost(route1, model)
# #             cost2 = get_route_cost(route2, model)
# #             for k in range(1, len(route1) - 1):
# #                 for l in range(1, len(route2) - 1):
# #                     # Swap nodes
# #                     temp_route1 = route1[:]
# #                     temp_route2 = route2[:]
# #                     temp_route1[k], temp_route2[l] = temp_route2[l], temp_route1[k]
# #                     new_load1 = load1 - model.nodes[route1[k]].demand + model.nodes[route2[l]].demand
# #                     new_load2 = load2 - model.nodes[route2[l]].demand + model.nodes[route1[k]].demand
# #                     if new_load1 > model.capacity or new_load2 > model.capacity:
# #                         continue
# #                     new_cost1 = get_route_cost(temp_route1, model)
# #                     new_cost2 = get_route_cost(temp_route2, model)
# #                     if new_cost1 > model.t_max or new_cost2 > model.t_max:
# #                         continue
# #                     if new_cost1 + new_cost2 < cost1 + cost2:
# #                         # Accept the swap
# #                         new_solution.routes[i] = temp_route1
# #                         new_solution.routes[j] = temp_route2
# #                         new_solution.update_all_metrics()
# #                         improved = True
# #                         break
# #                 if improved:
# #                     break
# #             if improved:
# #                 break
# #         if improved:
# #             break
# #     return new_solution
    

# # # def two_opt(solution, model):
# # #     # Implement the 2-opt algorithm for route improvement
# # #     new_solution = solution.copy()
# # #     for route in new_solution.routes:
# # #         if len(route) <= 3:  # Not enough nodes to perform 2-opt (excluding depot)
# # #             continue
# # #         best_cost = float('inf')
# # #         best_route = route.copy()
# # #         for i in range(1, len(route) - 2):
# # #             for j in range(i + 2, len(route) - 1):
# # #                 # Perform 2-opt swap by reversing the segment between i and j
# # #                 new_route = route[:i] + route[i:j][::-1] + route[j:]
# # #                 new_route.update_all_metrics()  # Update metrics after swap
# # #                 if new_route.total_cost < best_cost:
# # #                     best_cost = new_route.total_cost
# # #                     best_route = new_route.copy()
# # #         route[:] = best_route[:]  # Update the original route with the best found
# # #     new_solution.update_all_metrics()  # Update metrics after all routes are processed
# # #     return new_solution


# # def get_route_cost(route, model):
# #     """Βοηθητική συνάρτηση για τον υπολογισμό του χρόνου μιας λίστας κόμβων."""
# #     cost = 0
# #     for i in range(len(route) - 1):
# #         cost += model.cost_matrix[route[i]][route[i+1]]
# #     return cost

# # def two_opt(solution, model):
# #     # Δημιουργούμε ένα βαθύ αντίγραφο για να μην επηρεάσουμε την αρχική λύση
# #     import copy
# #     new_solution = copy.deepcopy(solution)
    
# #     for r_idx, route in enumerate(new_solution.routes):
# #         if len(route) <= 4:  # Χρειαζόμαστε τουλάχιστον 4 κόμβους (π.χ. [0, A, B, 0])
# #             continue
            
# #         improved = True
# #         while improved:
# #             improved = False
# #             best_cost = get_route_cost(route, model)
            
# #             # i: το σημείο πρώτης κοπής, j: το σημείο δεύτερης κοπής
# #             for i in range(1, len(route) - 2):
# #                 for j in range(i + 1, len(route) - 1):
# #                     # Αντιστροφή του τμήματος μεταξύ i και j
# #                     # Το [i:j+1][::-1] αντιστρέφει το κομμάτι της διαδρομής
# #                     new_route = route[:i] + route[i:j+1][::-1] + route[j+1:]
                    
# #                     new_cost = get_route_cost(new_route, model)
                    
# #                     if new_cost < best_cost:
# #                         route = new_route[:]
# #                         best_cost = new_cost
# #                         improved = True
            
# #             # Ενημέρωση της διαδρομής στο αντικείμενο solution
# #             new_solution.routes[r_idx] = route

# #     # Στο τέλος ενημερώνουμε όλα τα metrics του αντικειμένου Solution
# #     new_solution.calculate_total_metrics() 
# #     return new_solution

# # def local_search(model, solution):

# #     improved = True

# #     current_solution = copy.deepcopy(solution)

# #     while improved:

# #         improved = False

# #         # intra swap
# #         new_solution = apply_intra_route_swap(current_solution, model)

# #         if new_solution.total_cost < current_solution.total_cost:
# #             current_solution = new_solution
# #             improved = True

# #         # inter swap
# #         new_solution = apply_inter_route_swap(current_solution, model)

# #         if new_solution.total_cost < current_solution.total_cost:
# #             current_solution = new_solution
# #             improved = True

# #         # 2-opt
# #         new_solution = two_opt(current_solution, model)

# #         if new_solution.total_cost < current_solution.total_cost:
# #             current_solution = new_solution
# #             improved = True

# #     return current_solution


# import copy
# from Solution import Route
# import Helpers




# def get_route_cost(nodes, model):
#     """
#     Υπολογίζει το συνολικό travel time μιας λίστας node ids.
#     """
#     cost = 0

#     for i in range(len(nodes) - 1):
#         cost += model.cost_matrix[nodes[i]][nodes[i + 1]]

#     return cost


# def calculate_route_load(nodes, model):

#     load = 0

#     for n in nodes:
#         load += model.nodes[n].demand

#     return load


# def calculate_route_profit(nodes, model):

#     profit = 0

#     for n in nodes:
#         profit += model.nodes[n].profit

#     return profit


# def update_route_metrics(route, model):

#     route.load = calculate_route_load(route.nodes, model)
#     route.time = get_route_cost(route.nodes, model)
#     route.profit = calculate_route_profit(route.nodes, model)


# def update_solution_metrics(solution, model):

#     solution.total_profit = 0
#     solution.total_time = 0
#     solution.total_load = 0

#     solution.visited = set()

#     for route in solution.routes:

#         update_route_metrics(route, model)

#         solution.total_profit += route.profit
#         solution.total_time += route.time
#         solution.total_load += route.load

#         for n in route.nodes:
#             if n != 0:
#                 solution.visited.add(n)


# # =========================================================
# # INTRA ROUTE SWAP
# # =========================================================

# def swap_intra_route(route, model):

#     nodes = route.nodes[:]

#     if len(nodes) <= 3:
#         return route, False

#     best_nodes = nodes[:]
#     best_cost = get_route_cost(nodes, model)
#     print("Current route cost:", best_cost)
#     improved = False

#     for i in range(1, len(nodes) - 1):

#         for j in range(i + 1, len(nodes) - 1):

#             temp_nodes = nodes[:]

#             temp_nodes[i], temp_nodes[j] = (
#                 temp_nodes[j],
#                 temp_nodes[i]
#             )

#             new_cost = get_route_cost(temp_nodes, model)

#             if new_cost < best_cost:

#                 best_cost = new_cost
#                 best_nodes = temp_nodes[:]

#                 improved = True

#     if improved:

#         route.nodes = best_nodes
#         update_route_metrics(route, model)

#     return route, improved


# def apply_intra_route_swap(solution, model):

#     new_solution = copy.deepcopy(solution)

#     for idx, route in enumerate(new_solution.routes):

#         improved_route, _ = swap_intra_route(route, model)

#         new_solution.routes[idx] = improved_route

#     update_solution_metrics(new_solution, model)

#     return new_solution


# # =========================================================
# # INTER ROUTE SWAP
# # =========================================================

# def apply_inter_route_swap(solution, model):

#     new_solution = copy.deepcopy(solution)

#     improved = False

#     for r1 in range(len(new_solution.routes)):

#         for r2 in range(r1 + 1, len(new_solution.routes)):

#             route1 = new_solution.routes[r1]
#             route2 = new_solution.routes[r2]

#             nodes1 = route1.nodes
#             nodes2 = route2.nodes

#             for i in range(1, len(nodes1) - 1):

#                 for j in range(1, len(nodes2) - 1):

#                     temp1 = nodes1[:]
#                     temp2 = nodes2[:]

#                     temp1[i], temp2[j] = temp2[j], temp1[i]

#                     load1 = calculate_route_load(temp1, model)
#                     load2 = calculate_route_load(temp2, model)

#                     if load1 > model.capacity:
#                         continue

#                     if load2 > model.capacity:
#                         continue

#                     cost1 = get_route_cost(temp1, model)
#                     cost2 = get_route_cost(temp2, model)

#                     if cost1 > model.t_max:
#                         continue

#                     if cost2 > model.t_max:
#                         continue

#                     old_total = (
#                         route1.time +
#                         route2.time
#                     )

#                     new_total = (
#                         cost1 +
#                         cost2
#                     )

#                     if new_total < old_total:

#                         route1.nodes = temp1
#                         route2.nodes = temp2

#                         update_route_metrics(route1, model)
#                         update_route_metrics(route2, model)

#                         improved = True

#                         break

#                 if improved:
#                     break

#             if improved:
#                 break

#         if improved:
#             break

#     update_solution_metrics(new_solution, model)

#     return new_solution


# # =========================================================
# # 2-OPT
# # =========================================================

# def two_opt(solution, model):

#     new_solution = copy.deepcopy(solution)

#     for r_idx, route in enumerate(new_solution.routes):

#         nodes = route.nodes[:]

#         if len(nodes) <= 4:
#             continue

#         improved = True

#         while improved:

#             improved = False

#             best_cost = get_route_cost(nodes, model)

#             for i in range(1, len(nodes) - 2):

#                 for j in range(i + 1, len(nodes) - 1):

#                     candidate = (
#                         nodes[:i]
#                         + nodes[i:j + 1][::-1]
#                         + nodes[j + 1:]
#                     )

#                     candidate_cost = get_route_cost(candidate, model)

#                     if candidate_cost < best_cost:

#                         nodes = candidate[:]

#                         best_cost = candidate_cost

#                         improved = True

#         route.nodes = nodes

#         update_route_metrics(route, model)

#     update_solution_metrics(new_solution, model)

#     return new_solution


# # =========================================================
# # LOCAL SEARCH
# # =========================================================

# def local_search(model, solution):

#     current_solution = copy.deepcopy(solution)

#     improved = True

#     while improved:
        
#         improved = False

#         old_cost = Helpers.calculate_total_cost(model, current_solution.routes)
#         print (old_cost)
#         old_profit = current_solution.total_profit 
#         old_time = current_solution.total_time

#         # ---------------------------------
#         # INTRA ROUTE SWAP
#         # ---------------------------------

#         candidate = apply_intra_route_swap(
#             current_solution,
#             model
#         )

#         if (
#             Helpers.calculate_total_cost(model, candidate.routes) < old_cost
#             or
#             (
#                 Helpers.calculate_total_cost(model, candidate.routes) == old_cost
#                 and candidate.total_time < old_time
#             )
#         ):

#             current_solution = candidate

#             improved = True

#             continue

#         # ---------------------------------
#         # INTER ROUTE SWAP
#         # ---------------------------------

#         candidate = apply_inter_route_swap(
#             current_solution,
#             model
#         )

#         if (
#             Helpers.calculate_total_cost(model, candidate.routes) < old_cost
#             or
#             (
#                 Helpers.calculate_total_cost(model, candidate.routes) == old_cost
#                 and candidate.total_time < old_time
#             )
#         ):

#             current_solution = candidate

#             improved = True

#             continue

#         # ---------------------------------
#         # 2 OPT
#         # ---------------------------------

#         candidate = two_opt(
#             current_solution,
#             model
#         )

#         if (
#             Helpers.calculate_total_cost(model, candidate.routes) < old_cost
#             or
#             (
#                 Helpers.calculate_total_cost(model, candidate.routes) == old_cost
#                 and candidate.total_time < old_time
#             )
#         ):
            

#             current_solution = candidate

#             improved = True

#     return current_solution



# LocalSearch.py
# LocalSearch.py
import copy


def _update_metrics(sol):
    """Ενημερώνει τα συνολικά metrics της λύσης από τα επιμέρους routes."""
    sol.total_profit = sum(r.profit for r in sol.routes)
    sol.total_time   = sum(r.time   for r in sol.routes)
    sol.total_load   = sum(r.load   for r in sol.routes)


def local_search(model, solution, enforce_mandatory=False):
    """
    Profit-focused local search για το Team Orienteering Problem.

    Αν enforce_mandatory=True:
      - Δεν αφαιρούνται ποτέ mandatory κόμβοι (node_exchange)
      - Mandatory κόμβοι εισάγονται πρώτοι (insert_unvisited)
      - Αν δεν χωράνε, αφαιρούνται optional κόμβοι για να κάνουν χώρο (force_insert_mandatory)

    Βήματα (επαναλαμβάνονται έως ότου δεν υπάρχει βελτίωση):
      1. force_insert_mandatory: εξασφαλίζει ότι όλοι οι mandatory κόμβοι είναι στη λύση
      2. node_exchange:          αντικατάσταση optional κόμβου με μη-επισκεφθέντα υψηλότερου κέρδους
      3. insert_unvisited:       εισαγωγή νέων κόμβων σε κενό χώρο
    """
    sol = copy.deepcopy(solution)

    improved = True
    while improved:
        improved = False

        # Βήμα 1: Εξασφάλιση mandatory κόμβων (μόνο αν enforce_mandatory=True)
        if enforce_mandatory:
            if _force_insert_mandatory(model, sol):
                improved = True

        # Βήμα 2: Αντικατάσταση κόμβων (ποτέ δεν αγγίζουμε mandatory)
        if _node_exchange(model, sol, enforce_mandatory):
            improved = True

        # Βήμα 3: Εισαγωγή νέων κόμβων (mandatory πρώτα αν enforce_mandatory)
        if _insert_unvisited(model, sol, enforce_mandatory):
            improved = True

    # Τελικό 2-opt: βελτίωση δομής routes χωρίς αλλαγή στους επισκεπτόμενους κόμβους
    _two_opt_all_routes(model, sol)
    _update_metrics(sol)

    return sol


# ─────────────────────────────────────────────
#  ΒΑΣΙΚΕΣ ΚΙΝΗΣΕΙΣ
# ─────────────────────────────────────────────

def _node_exchange(model, sol, enforce_mandatory=False):
    """
    Για κάθε κόμβο i στις διαδρομές, ψάχνει μη-επισκεφθέντα κόμβο j
    με μεγαλύτερο κέρδος που μπορεί να τον αντικαταστήσει (feasibility check).

    Αν enforce_mandatory=True: παραλείπει mandatory κόμβους ως υποψήφιους για αφαίρεση —
    δεν επιτρέπεται να βγει mandatory κόμβος από route.

    Επιστρέφει True αν έγινε τουλάχιστον μία βελτίωση.
    """
    improved  = False
    all_nodes = set(range(1, model.num_nodes))
    unvisited = all_nodes - sol.visited

    # Ταξινόμηση μη-επισκεφθέντων κατά φθίνον κέρδος
    unvisited_sorted = sorted(unvisited, key=lambda n: model.nodes[n].profit, reverse=True)

    for route in sol.routes:
        for pos in range(1, len(route.nodes) - 1):
            node_i    = route.nodes[pos]
            prev_node = route.nodes[pos - 1]
            next_node = route.nodes[pos + 1]

            # ΚΑΝΟΝΑΣ MANDATORY: δεν αφαιρούμε ποτέ mandatory κόμβο
            if enforce_mandatory and model.nodes[node_i].isMandatory:
                continue

            # Χρόνος που εξοικονομείται αφαιρώντας τον node_i
            time_saved = (
                model.cost_matrix[prev_node][node_i]
                + model.cost_matrix[node_i][next_node]
                - model.cost_matrix[prev_node][next_node]
            )

            for node_j in unvisited_sorted:
                # Δεν έχει νόημα swap αν ο j δεν έχει μεγαλύτερο κέρδος
                if model.nodes[node_j].profit <= model.nodes[node_i].profit:
                    break

                # Επιπλέον χρόνος από εισαγωγή του node_j στη θέση pos
                time_added = (
                    model.cost_matrix[prev_node][node_j]
                    + model.cost_matrix[node_j][next_node]
                    - model.cost_matrix[prev_node][next_node]
                )

                net_time_change   = time_added - time_saved
                net_demand_change = model.nodes[node_j].demand - model.nodes[node_i].demand

                # Έλεγχος περιορισμού χωρητικότητας
                if route.load + net_demand_change > model.capacity:
                    continue

                # Έλεγχος περιορισμού χρόνου
                if route.time + net_time_change > model.t_max:
                    continue

                # Εκτέλεση swap
                route.nodes[pos] = node_j
                route.load       += net_demand_change
                route.time       += net_time_change
                route.profit     += model.nodes[node_j].profit - model.nodes[node_i].profit

                sol.visited.discard(node_i)
                sol.visited.add(node_j)
                unvisited.discard(node_j)
                unvisited.add(node_i)

                # Ενημέρωση ταξινομημένης λίστας μετά το swap
                unvisited_sorted = sorted(
                    unvisited, key=lambda n: model.nodes[n].profit, reverse=True
                )

                improved = True
                break  # Επόμενη θέση στο route

    _update_metrics(sol)
    return improved


def _insert_unvisited(model, sol, enforce_mandatory=False):
    """
    Δοκιμάζει να εισάγει μη-επισκεφθέντους κόμβους στη φτηνότερη feasible θέση.

    Αν enforce_mandatory=True: οι mandatory κόμβοι μπαίνουν πρώτοι στη λίστα,
    ανεξάρτητα από κέρδος — εξασφάλιση έγκυρης λύσης.

    Επιστρέφει True αν εισήχθη τουλάχιστον ένας κόμβος.
    """
    improved  = False
    all_nodes = set(range(1, model.num_nodes))
    unvisited = all_nodes - sol.visited

    if enforce_mandatory:
        # Mandatory κόμβοι πρώτοι, μετά optional κατά φθίνον κέρδος
        mandatory_unvisited = sorted(
            [n for n in unvisited if model.nodes[n].isMandatory],
            key=lambda n: model.nodes[n].profit,
            reverse=True
        )
        optional_unvisited = sorted(
            [n for n in unvisited if not model.nodes[n].isMandatory],
            key=lambda n: model.nodes[n].profit,
            reverse=True
        )
        ordered_unvisited = mandatory_unvisited + optional_unvisited
    else:
        # Χωρίς mandatory constraint: απλή ταξινόμηση κατά κέρδος
        ordered_unvisited = sorted(unvisited, key=lambda n: model.nodes[n].profit, reverse=True)

    for node in ordered_unvisited:
        best_route = None
        best_pos   = None
        best_delta = float("inf")

        for route in sol.routes:
            for pos in range(1, len(route.nodes)):
                a = route.nodes[pos - 1]
                b = route.nodes[pos]

                # Επιπλέον χρόνος από εισαγωγή του node μεταξύ a και b
                delta = (
                    model.cost_matrix[a][node]
                    + model.cost_matrix[node][b]
                    - model.cost_matrix[a][b]
                )

                # Έλεγχος χωρητικότητας
                if route.load + model.nodes[node].demand > model.capacity:
                    continue

                # Έλεγχος χρόνου
                if route.time + delta > model.t_max:
                    continue

                # Greedy: επιλογή φτηνότερης εισαγωγής
                if delta < best_delta:
                    best_delta = delta
                    best_route = route
                    best_pos   = pos

        if best_route is not None:
            best_route.nodes.insert(best_pos, node)
            best_route.load   += model.nodes[node].demand
            best_route.time   += best_delta
            best_route.profit += model.nodes[node].profit
            sol.visited.add(node)
            improved = True

    _update_metrics(sol)
    return improved


def _force_insert_mandatory(model, sol):
    """
    Εξασφαλίζει ότι ΟΛΟΙ οι mandatory κόμβοι βρίσκονται στη λύση.

    Για κάθε mandatory κόμβο που λείπει:
      1. Δοκιμάζει απευθείας εισαγωγή σε κάθε route (χωρίς αφαίρεση).
      2. Αν δεν χωράει πουθενά, αφαιρεί τον optional κόμβο με το
         χειρότερο profit/demand ratio από κάθε route και ξαναδοκιμάζει.

    Αυτό εγγυάται feasibility για το mandatory constraint ακόμα και αν
    αρχικά δεν υπάρχει χώρος.

    Επιστρέφει True αν έγινε τουλάχιστον μία εισαγωγή mandatory κόμβου.
    """
    improved = False

    # Εύρεση mandatory κόμβων που λείπουν από τη λύση
    missing_mandatory = [
        node.id
        for node in model.nodes
        if node.isMandatory and node.id not in sol.visited
    ]

    for mand_node in missing_mandatory:

        inserted = _try_direct_insert(model, sol, mand_node)

        if not inserted:
            # Δεν χωράει απευθείας → αφαιρούμε τον "χειρότερο" optional κόμβο
            inserted = _make_room_and_insert(model, sol, mand_node)

        if inserted:
            improved = True

    _update_metrics(sol)
    return improved


def _try_direct_insert(model, sol, node):
    """
    Δοκιμάζει να εισάγει τον κόμβο node στη φτηνότερη feasible θέση
    χωρίς να αφαιρέσει κανέναν άλλο κόμβο.

    Επιστρέφει True αν η εισαγωγή πέτυχε.
    """
    best_route = None
    best_pos   = None
    best_delta = float("inf")

    for route in sol.routes:
        for pos in range(1, len(route.nodes)):
            a = route.nodes[pos - 1]
            b = route.nodes[pos]

            delta = (
                model.cost_matrix[a][node]
                + model.cost_matrix[node][b]
                - model.cost_matrix[a][b]
            )

            # Έλεγχος χωρητικότητας
            if route.load + model.nodes[node].demand > model.capacity:
                continue

            # Έλεγχος χρόνου
            if route.time + delta > model.t_max:
                continue

            if delta < best_delta:
                best_delta = delta
                best_route = route
                best_pos   = pos

    if best_route is not None:
        best_route.nodes.insert(best_pos, node)
        best_route.load   += model.nodes[node].demand
        best_route.time   += best_delta
        best_route.profit += model.nodes[node].profit
        sol.visited.add(node)
        return True

    return False


def _make_room_and_insert(model, sol, mand_node):
    """
    Για κάθε route, βρίσκει τον optional κόμβο με το χειρότερο
    profit/demand ratio, τον αφαιρεί προσωρινά, και δοκιμάζει
    να εισάγει τον mandatory κόμβο.

    Αν η εισαγωγή πετύχει: η αφαίρεση γίνεται μόνιμη.
    Αν όχι: επαναφέρει τον optional κόμβο.

    Επιστρέφει True αν η εισαγωγή πέτυχε.
    """
    for route in sol.routes:

        # Εύρεση του worst optional κόμβου στο route
        worst_pos   = None
        worst_score = float("inf")

        for pos in range(1, len(route.nodes) - 1):
            candidate = route.nodes[pos]

            # Ποτέ δεν αφαιρούμε mandatory κόμβο για να κάνουμε χώρο
            if model.nodes[candidate].isMandatory:
                continue

            profit = model.nodes[candidate].profit
            demand = model.nodes[candidate].demand

            # Score: profit/demand — χαμηλό score = λιγότερο αξιόλογος κόμβος
            score = profit / demand if demand > 0 else profit

            if score < worst_score:
                worst_score = score
                worst_pos   = pos

        if worst_pos is None:
            # Το route έχει μόνο mandatory κόμβους — δεν μπορούμε να αφαιρέσουμε τίποτα
            continue

        # Αφαίρεση του worst optional (προσωρινά)
        removed_node    = route.nodes[worst_pos]
        prev_n          = route.nodes[worst_pos - 1]
        next_n          = route.nodes[worst_pos + 1]

        time_freed = (
            model.cost_matrix[prev_n][removed_node]
            + model.cost_matrix[removed_node][next_n]
            - model.cost_matrix[prev_n][next_n]
        )

        route.nodes.pop(worst_pos)
        route.load   -= model.nodes[removed_node].demand
        route.time   -= time_freed
        route.profit -= model.nodes[removed_node].profit
        sol.visited.discard(removed_node)

        # Δοκιμή εισαγωγής του mandatory στο τώρα ελεύθερο route
        inserted = _try_direct_insert(model, sol, mand_node)

        if inserted:
            # Εισαγωγή πέτυχε — ο removed_node παραμένει εκτός
            return True
        else:
            # Δεν χωράει ακόμα — επαναφορά του removed_node
            route.nodes.insert(worst_pos, removed_node)
            route.load   += model.nodes[removed_node].demand
            route.time   += time_freed
            route.profit += model.nodes[removed_node].profit
            sol.visited.add(removed_node)

    return False


# ─────────────────────────────────────────────
#  ΒΟΗΘΗΤΙΚΗ: 2-OPT
# ─────────────────────────────────────────────

def _two_opt_route(model, route):
    """
    2-opt σε ένα route: αντιστρέφει τμήματα για μείωση χρόνου.
    ΔΕΝ αλλάζει ποιοι κόμβοι επισκέπτονται — μόνο τη σειρά τους.
    """
    improved = True
    while improved:
        improved = False
        n = len(route.nodes)

        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                cost_before = (
                    model.cost_matrix[route.nodes[i - 1]][route.nodes[i]]
                    + model.cost_matrix[route.nodes[j]][route.nodes[j + 1]]
                )
                cost_after = (
                    model.cost_matrix[route.nodes[i - 1]][route.nodes[j]]
                    + model.cost_matrix[route.nodes[i]][route.nodes[j + 1]]
                )

                if cost_after < cost_before:
                    # Αντιστροφή τμήματος [i..j]
                    route.nodes[i:j + 1] = route.nodes[i:j + 1][::-1]
                    route.time -= (cost_before - cost_after)
                    improved    = True


def _two_opt_all_routes(model, sol):
    """Εφαρμόζει 2-opt σε όλα τα routes της λύσης."""
    for route in sol.routes:
        if len(route.nodes) > 3:
            _two_opt_route(model, route)