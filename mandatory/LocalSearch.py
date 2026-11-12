import copy

def _or_opt_relocate(model, sol, enforce_mandatory=False):
    """
    Or-opt: Μεταφέρει έναν κόμβο από route A σε route B.

    Γιατί βοηθάει στο TOP (Dang et al. 2013):
    Ένας κόμβος που "χάνει" χρόνο στο route A ίσως ταιριάζει καλύτερα
    στο route B. Ο ελεύθερος χρόνος στο A επιτρέπει εισαγωγή νέου
    high-profit κόμβου. Έτσι ξεφεύγουμε από local optima που το
    node_exchange δεν μπορεί να λύσει.
    """
    improved = False

    for r1_idx in range(len(sol.routes)):
        route1 = sol.routes[r1_idx]

        for pos in range(1, len(route1.nodes) - 1):
            node_v = route1.nodes[pos]

            # Ποτέ δε μετακινούμε mandatory κόμβο
            if enforce_mandatory and model.nodes[node_v].isMandatory:
                continue

            prev1 = route1.nodes[pos - 1]
            next1 = route1.nodes[pos + 1]

            # Χρόνος που ελευθερώνεται από το route1 αφαιρώντας node_v
            time_freed_r1 = (
                model.cost_matrix[prev1][node_v]
                + model.cost_matrix[node_v][next1]
                - model.cost_matrix[prev1][next1]
            )

            # Δοκιμή εισαγωγής node_v σε κάθε άλλο route
            for r2_idx in range(len(sol.routes)):
                if r2_idx == r1_idx:
                    continue

                route2 = sol.routes[r2_idx]

                # Εύρεση καλύτερης θέσης στο route2 για τον node_v
                best_pos2  = None
                best_delta2 = float("inf")

                for pos2 in range(1, len(route2.nodes)):
                    a2 = route2.nodes[pos2 - 1]
                    b2 = route2.nodes[pos2]

                    delta2 = (
                        model.cost_matrix[a2][node_v]
                        + model.cost_matrix[node_v][b2]
                        - model.cost_matrix[a2][b2]
                    )

                    if route2.load + model.nodes[node_v].demand > model.capacity:
                        continue
                    if route2.time + delta2 > model.t_max:
                        continue

                    if delta2 < best_delta2:
                        best_delta2 = delta2
                        best_pos2   = pos2

                if best_pos2 is None:
                    continue  # Δεν χωράει στο route2

                # node_v χωράει στο route2 — τώρα ψάχνουμε αν ο
                # ελεύθερος χρόνος στο route1 επιτρέπει καλύτερο κόμβο
                unvisited = set(range(1, model.num_nodes)) - sol.visited

                best_new_node  = None
                best_new_pos1  = None
                best_new_delta1 = float("inf")
                best_new_profit = model.nodes[node_v].profit  # baseline: τουλάχιστον ίδιο profit

                # Υπολογισμός metrics του route1 ΧΩΡΙΣ τον node_v
                new_route1_load = route1.load - model.nodes[node_v].demand
                new_route1_time = route1.time - time_freed_r1

                for new_node in unvisited:
                    if model.nodes[new_node].profit <= best_new_profit:
                        continue  # Θέλουμε αυστηρά καλύτερο profit

                    for ins_pos in range(1, len(route1.nodes) - 1):
                        # Παράλειψη θέσης pos (θα αφαιρεθεί)
                        if ins_pos == pos:
                            continue

                        # Κόμβοι γύρω από τη θέση εισαγωγής (στο route1 ΧΩΡΙΣ node_v)
                        temp_nodes = route1.nodes[:pos] + route1.nodes[pos+1:]
                        if ins_pos >= pos:
                            ins_pos_adj = ins_pos - 1
                        else:
                            ins_pos_adj = ins_pos

                        if ins_pos_adj < 1 or ins_pos_adj >= len(temp_nodes):
                            continue

                        a1 = temp_nodes[ins_pos_adj - 1]
                        b1 = temp_nodes[ins_pos_adj]

                        delta1 = (
                            model.cost_matrix[a1][new_node]
                            + model.cost_matrix[new_node][b1]
                            - model.cost_matrix[a1][b1]
                        )

                        if new_route1_load + model.nodes[new_node].demand > model.capacity:
                            continue
                        if new_route1_time + delta1 > model.t_max:
                            continue

                        if model.nodes[new_node].profit > best_new_profit:
                            best_new_profit  = model.nodes[new_node].profit
                            best_new_node    = new_node
                            best_new_pos1    = ins_pos_adj
                            best_new_delta1  = delta1

                # Αν βρήκαμε νέο κόμβο με καλύτερο profit: εκτέλεση κίνησης
                if best_new_node is not None:
                    # 1. Αφαίρεση node_v από route1
                    route1.nodes.pop(pos)
                    route1.load   -= model.nodes[node_v].demand
                    route1.time   -= time_freed_r1
                    route1.profit -= model.nodes[node_v].profit

                    # 2. Εισαγωγή new_node στο route1
                    route1.nodes.insert(best_new_pos1, best_new_node)
                    route1.load   += model.nodes[best_new_node].demand
                    route1.time   += best_new_delta1
                    route1.profit += model.nodes[best_new_node].profit

                    # 3. Εισαγωγή node_v στο route2
                    route2.nodes.insert(best_pos2, node_v)
                    route2.load   += model.nodes[node_v].demand
                    route2.time   += best_delta2
                    route2.profit += model.nodes[node_v].profit

                    # 4. Ενημέρωση visited
                    sol.visited.discard(node_v)   # βγαίνει από route1
                    sol.visited.add(node_v)        # μπαίνει στο route2
                    sol.visited.add(best_new_node)

                    _update_metrics(sol)
                    improved = True
                    break  # Restart από την αρχή

            if improved:
                break
        if improved:
            break

    return improved



def _update_metrics(sol):
    """Ενημερώνει τα συνολικά metrics της λύσης από τα επιμέρους routes."""
    sol.total_profit = sum(r.profit for r in sol.routes)
    sol.total_time   = sum(r.time   for r in sol.routes)
    sol.total_load   = sum(r.load   for r in sol.routes)

def local_search(model, solution, enforce_mandatory=False,
                 max_passes=999, apply_two_opt=True):
    """
    max_passes=1
    max_passes=999
    apply_two_opt=False → παράλειψη 2-opt στο τέλος (για πιο γρήγορη εκτέλεση)
    """
    sol = copy.deepcopy(solution)

    for _ in range(max_passes):
        improved = False

        if enforce_mandatory:
            if _force_insert_mandatory(model, sol):
                improved = True

        if _node_exchange(model, sol, enforce_mandatory):
            improved = True

        if _or_opt_relocate(model, sol, enforce_mandatory):
            improved = True

        sol, success_2 = _multi_node_exchange(model, sol, num_nodes_to_remove=2, enforce_mandatory=enforce_mandatory)
        if success_2:
            improved = True

        sol, success_3 = _multi_node_exchange(model, sol, num_nodes_to_remove=3, enforce_mandatory=enforce_mandatory)
        if success_3:
            improved = True


        if _insert_unvisited(model, sol, enforce_mandatory):
            improved = True

        if not improved:
            break

    if apply_two_opt:
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

                # Πρόσθετος χρόνος από εισαγωγή του node_j στη θέση pos
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


def _multi_node_exchange(model, solution, num_nodes_to_remove=2, enforce_mandatory=False):
    """
    Αφαιρεί num_nodes_to_remove συνεχόμενους κόμβους από μια διαδρομή
    και δοκιμάζει να εισάγει έναν unvisited κόμβο που προσφέρει μεγαλύτερο profit
    εκμεταλλευόμενος τον μεγάλο χώρο/χρόνο που ελευθερώθηκε.

    Αν enforce_mandatory=True, διασφαλίζει ότι κανένας mandatory κόμβος
    δε θα αφαιρεθεί από τη λύση.
    """
    sol = copy.deepcopy(solution)
    unvisited = set(range(1, model.num_nodes)) - sol.visited

    for route in sol.routes:
        # Χρειαζόμαστε αρκετούς κόμβους στη διαδρομή (μαζί με τα depot)
        if len(route.nodes) < num_nodes_to_remove + 3:
            continue

        # i: η θέση έναρξης της αφαίρεσης
        for i in range(1, len(route.nodes) - num_nodes_to_remove):
            # Προσδιορισμός των κόμβων προς αφαίρεση
            removed_indices = list(range(i, i + num_nodes_to_remove))
            nodes_to_remove = [route.nodes[idx] for idx in removed_indices]

            # 🌟 ΚΑΝΟΝΑΣ MANDATORY: Αν ζητάμε έγκυρη mandatory λύση,
            # ελέγχουμε αν ανάμεσα στους κόμβους προς αφαίρεση υπάρχει έστω και ένας υποχρεωτικός.
            if enforce_mandatory:
                contains_mandatory = any(model.nodes[n].isMandatory for n in nodes_to_remove)
                if contains_mandatory:
                    continue  # Προσπέραση αυτού του συνδυασμού, δεν επιτρέπεται η αφαίρεση

            A = route.nodes[i - 1]
            B = route.nodes[i + num_nodes_to_remove]

            # Υπολογισμός των metrics που απελευθερώνονται
            saved_load = sum(model.nodes[n].demand for n in nodes_to_remove)
            saved_profit = sum(model.nodes[n].profit for n in nodes_to_remove)

            # Χρόνος της παλιάς υπο-διαδρομής
            old_sub_time = model.cost_matrix[A][nodes_to_remove[0]]
            for k in range(len(nodes_to_remove) - 1):
                old_sub_time += model.cost_matrix[nodes_to_remove[k]][nodes_to_remove[k+1]]
            old_sub_time += model.cost_matrix[nodes_to_remove[-1]][B]

            # Δοκιμή αντικατάστασης με ΕΝΑΝ καλό unvisited κόμβο j
            for j in unvisited:
                if model.nodes[j].profit <= saved_profit:
                    continue  # Θέλουμε αυστηρά μεγαλύτερο profit

                new_load = route.load - saved_load + model.nodes[j].demand
                if new_load > model.capacity:
                    continue

                added_time = model.cost_matrix[A][j] + model.cost_matrix[j][B]
                new_time = route.time - old_sub_time + added_time
                if new_time > model.t_max:
                    continue

                # Αν φτάσαμε εδώ, το swap είναι feasible και κερδοφόρο!
                # 1. Αφαίρεση των παλιών κόμβων (pop από το τέλος προς την αρχή για να μην χαλάσουν τα indices)
                for idx in reversed(removed_indices):
                    route.nodes.pop(idx)

                # 2. Εισαγωγή του νέου κόμβου
                route.nodes.insert(i, j)

                # 3. Ενημέρωση metrics διαδρομής
                route.load = new_load
                route.time = new_time
                route.profit = route.profit - saved_profit + model.nodes[j].profit

                # 4. Ενημέρωση visited sets
                for n in nodes_to_remove:
                    sol.visited.remove(n)
                sol.visited.add(j)

                # Ενημέρωση γενικών metrics λύσης και επιστροφή
                sol.total_profit = sum(r.profit for r in sol.routes)
                sol.total_time = sum(r.time for r in sol.routes)
                sol.total_load = sum(r.load for r in sol.routes)
                return sol, True

    return sol, False


def _net_profit_global_exchange(model, sol, enforce_mandatory=False,
                                profit_threshold=None):
    """
    Multi-drop exchange: αφαιρεί συνδυαστικά optional κόμβους χαμηλού
    profit/demand ratio για να κάνει χώρο σε unvisited κόμβο υψηλού profit.

    Λειτουργεί και για capacity-full ΚΑΙ time-full routes.

    profit_threshold=None → adaptive: top 20% unvisited κατά profit
    """
    all_nodes = set(range(1, model.num_nodes))
    unvisited  = all_nodes - sol.visited

    if not unvisited:
        return sol, False

    # ── Threshold: adaptive αν δεν δοθεί ────────────────────────────────────
    if profit_threshold is None:
        profits = sorted([model.nodes[n].profit for n in unvisited], reverse=True)
        # Top 20% των unvisited κατά profit
        cutoff_idx       = max(0, int(len(profits) * 0.2) - 1)
        profit_threshold = profits[cutoff_idx] if profits else 0

    # ── Βήμα 1: Unvisited στόχοι με profit >= threshold ─────────────────────
    targets = sorted(
        [n for n in unvisited if model.nodes[n].profit >= profit_threshold],
        key=lambda n: model.nodes[n].profit,
        reverse=True
    )

    if not targets:
        return sol, False

    for target_node in targets:
        target_profit = model.nodes[target_node].profit
        target_demand = model.nodes[target_node].demand
        target_ratio  = target_profit / max(target_demand, 1)

        # ── Βήμα 2: Σάρωση routes ───────────────────────────────────────────
        for route in sol.routes:

            # Συλλογή optional κόμβων που έχουν ratio <= target (υποψήφιοι αφαίρεσης)
            removable = []
            for pos in range(1, len(route.nodes) - 1):
                node = route.nodes[pos]

                if enforce_mandatory and model.nodes[node].isMandatory:
                    continue  # Ποτέ δεν αγγίζουμε mandatory

                node_ratio = model.nodes[node].profit / max(model.nodes[node].demand, 1)
                if node_ratio <= target_ratio:
                    removable.append((node_ratio, pos, node))

            if not removable:
                continue

            # Χειρότερο ratio πρώτα
            removable.sort(key=lambda x: x[0])

            # ── Βήμα 3: Σταδιακή εκκένωση μέχρι να χωράει ──────────────────
            freed_demand = 0
            freed_profit = 0
            nodes_to_remove = []

            for _, pos, node in removable:
                nodes_to_remove.append((pos, node))
                freed_demand += model.nodes[node].demand
                freed_profit += model.nodes[node].profit

                # Έλεγχος capacity: χωράει τώρα;
                new_load = route.load - freed_demand + target_demand
                if new_load <= model.capacity:
                    break

            # Capacity check
            new_load = route.load - freed_demand + target_demand
            if new_load > model.capacity:
                continue

            # ── Βήμα 4: Net Profit check ─────────────────────────────────────
            net_gain = target_profit - freed_profit
            if net_gain <= 0:
                continue  # Δεν αξίζει

            # ── Βήμα 5: Κατασκευή route χωρίς αφαιρεθέντες ─────────────────
            remove_positions = {pos for pos, _ in nodes_to_remove}
            new_nodes = [
                n for idx, n in enumerate(route.nodes)
                if idx not in remove_positions
            ]

            # Χρόνος route ΧΩΡΙΣ αφαιρεθέντες (base για time check)
            base_time = sum(
                model.cost_matrix[new_nodes[i]][new_nodes[i + 1]]
                for i in range(len(new_nodes) - 1)
            )

            # ── Βήμα 6: Εύρεση καλύτερης θέσης εισαγωγής ───────────────────
            best_ins_pos = None
            best_delta   = float("inf")

            for ins_pos in range(1, len(new_nodes)):
                a = new_nodes[ins_pos - 1]
                b = new_nodes[ins_pos]

                delta = (
                    model.cost_matrix[a][target_node]
                    + model.cost_matrix[target_node][b]
                    - model.cost_matrix[a][b]
                )

                # Time check με το νέο base_time (μετά αφαιρέσεις)
                if base_time + delta <= model.t_max and delta < best_delta:
                    best_delta   = delta
                    best_ins_pos = ins_pos

            if best_ins_pos is None:
                continue  # Δεν χωράει χρονικά

            # ── Βήμα 7: Εφαρμογή ────────────────────────────────────────────
            final_nodes = (
                new_nodes[:best_ins_pos]
                + [target_node]
                + new_nodes[best_ins_pos:]
            )
            route.nodes = final_nodes

            # υπολογισμός metrics route
            route.load   = sum(model.nodes[n].demand for n in final_nodes if n != 0)
            route.time   = sum(
                model.cost_matrix[final_nodes[i]][final_nodes[i + 1]]
                for i in range(len(final_nodes) - 1)
            )
            route.profit = sum(model.nodes[n].profit for n in final_nodes if n != 0)

            # Ενημέρωση visited
            for _, removed_node in nodes_to_remove:
                sol.visited.discard(removed_node)
            sol.visited.add(target_node)

            _update_metrics(sol)
            return sol, True

    return sol, False
