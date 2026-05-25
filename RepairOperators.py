import copy


def update_solution_metrics(solution):

    solution.total_profit = sum(r.profit for r in solution.routes)
    solution.total_time = sum(r.time for r in solution.routes)
    solution.total_load = sum(r.load for r in solution.routes)

def feasible_insertion(model, route, node, delta):

    if route.load + model.nodes[node].demand > model.capacity:
        return False

    if route.time + delta > model.t_max:
        return False

    return True

def greedy_repair(model, partial_solution, removed_nodes):

    sol = copy.deepcopy(partial_solution)

    for node in removed_nodes:

        best_route = None
        best_pos = None
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

                if not feasible_insertion(
                    model,
                    route,
                    node,
                    delta
                ):
                    continue

                if delta < best_delta:

                    best_delta = delta
                    best_route = route
                    best_pos = pos

        if best_route is not None:

            best_route.nodes.insert(best_pos, node)

            best_route.load += model.nodes[node].demand
            best_route.time += best_delta
            best_route.profit += model.nodes[node].profit

    update_solution_metrics(sol)

    return sol


import random


def random_repair(model, partial_solution, removed_nodes):

    sol = copy.deepcopy(partial_solution)

    random.shuffle(removed_nodes)

    for node in removed_nodes:

        inserted = False

        routes = sol.routes[:]
        random.shuffle(routes)

        for route in routes:

            positions = list(range(1, len(route.nodes)))
            random.shuffle(positions)

            for pos in positions:

                a = route.nodes[pos - 1]
                b = route.nodes[pos]

                delta = (
                    model.cost_matrix[a][node]
                    + model.cost_matrix[node][b]
                    - model.cost_matrix[a][b]
                )

                if feasible_insertion(model, route, node, delta):

                    route.nodes.insert(pos, node)

                    route.load += model.nodes[node].demand
                    route.time += delta
                    route.profit += model.nodes[node].profit

                    inserted = True
                    break

            if inserted:
                break

    update_solution_metrics(sol)

    return sol

def regret_two_repair(model, partial_solution, removed_nodes):
    """
    Regret-2 Repair: Επιλέγει να εισάγει πρώτο τον κόμβο που έχει τη 
    μεγαλύτερη απώλεια (regret) αν δεν μπει στην ιδανική του διαδρομή.
    """
    sol = copy.deepcopy(partial_solution)
    nodes_to_insert = removed_nodes[:]

    while nodes_to_insert:
        node_regrets = []

        for node_id in nodes_to_insert:
            node = model.nodes[node_id]
            insertion_options = []

            # Υπολογισμός κόστους εισαγωγής σε κάθε feasible θέση όλων των routes
            for r_idx, route in enumerate(sol.routes):
                for pos in range(1, len(route.nodes)):
                    a = route.nodes[pos - 1]
                    b = route.nodes[pos]

                    delta_time = (model.cost_matrix[a][node_id] + 
                                  model.cost_matrix[node_id][b] - 
                                  model.cost_matrix[a][b])

                    if route.load + node.demand <= model.capacity:
                        if route.time + delta_time <= model.t_max:
                            # Evaluation score: θέλουμε μικρό delta_time ανά μονάδα profit
                            score = delta_time / max(1, node.profit)
                            insertion_options.append((score, r_idx, pos))

            # Ταξινόμηση επιλογών από την καλύτερη στη χειρότερη
            insertion_options.sort(key=lambda x: x[0])

            if not insertion_options:
                continue  # Ο κόμβος δε χωράει πουθενά

            if len(insertion_options) >= 2:
                # Regret = Το σκορ της 2ης καλύτερης θέσης ΜΕΙΟΝ της 1ης καλύτερης
                regret = insertion_options[1][0] - insertion_options[0][0]
            else:
                # Αν χωράει μόνο σε μία θέση, του δίνουμε ένα μεγάλο σταθερό regret
                regret = insertion_options[0][0] + 1000.0

            node_regrets.append((regret, node_id, insertion_options[0]))

        if not node_regrets:
            break  # Δε χωράει κανένας άλλος κόμβος

        # Επιλέγουμε τον κόμβο με το ΜΕΓΑΛΥΤΕΡΟ regret
        node_regrets.sort(key=lambda x: x[0], reverse=True)
        _, best_node_id, best_option = node_regrets[0]
        _, r_idx, pos = best_option

        # Εκτέλεση της εισαγωγής
        route = sol.routes[r_idx]
        node = model.nodes[best_node_id]
        
        a = route.nodes[pos - 1]
        b = route.nodes[pos]
        delta_time = (model.cost_matrix[a][best_node_id] + 
                      model.cost_matrix[best_node_id][b] - 
                      model.cost_matrix[a][b])

        route.nodes.insert(pos, best_node_id)
        route.load += node.demand
        route.time += delta_time
        route.profit += node.profit
        sol.visited.add(best_node_id)

        nodes_to_insert.remove(best_node_id)

    # Ενημέρωση των metrics της λύσης
    sol.total_profit = sum(r.profit for r in sol.routes)
    sol.total_time = sum(r.time for r in sol.routes)
    sol.total_load = sum(r.load for r in sol.routes)
    return sol

def minimum_repair(model, partial_solution, removed_nodes):

    sol = copy.deepcopy(partial_solution)
    #sort first if they are mandatory or not
    removed_nodes.sort(key=lambda x: model.nodes[x].isMandatory, reverse=True)
    for node in removed_nodes:
        
        best_route = None
        best_pos = None
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

                if not feasible_insertion(
                    model,
                    route,
                    node,
                    delta
                ):
                    continue

                if delta < best_delta:

                    best_delta = delta
                    best_route = route
                    best_pos = pos

        if best_route is not None:

            best_route.nodes.insert(best_pos, node)

            best_route.load += model.nodes[node].demand
            best_route.time += best_delta
            best_route.profit += model.nodes[node].profit

    update_solution_metrics(sol)

    return sol
        
    
