# # PathRelinking.py
# import copy
# import random


# def _update_metrics(sol):
#     """Ενημερώνει τα συνολικά metrics από τα επιμέρους routes."""
#     sol.total_profit = sum(r.profit for r in sol.routes)
#     sol.total_time   = sum(r.time   for r in sol.routes)
#     sol.total_load   = sum(r.load   for r in sol.routes)


# class EliteSet:
#     """
#     Κρατάει τις k καλύτερες λύσεις που έχουν βρεθεί κατά την αναζήτηση.
#     Χρησιμοποιείται ως πηγή "στόχων" για το Path Relinking.
#     """

#     def __init__(self, max_size=5):
#         self.max_size  = max_size
#         self.solutions = []  # Ταξινομημένη λίστα, καλύτερη πρώτη

#     def try_add(self, solution):
#         """
#         Προσπαθεί να εισάγει τη λύση στο elite set.
#         Αγνοεί λύσεις με ίδιο profit (αποφυγή διπλοτύπων).
#         """
#         # Έλεγχος για διπλότυπο
#         existing_profits = {s.total_profit for s in self.solutions}
#         if solution.total_profit in existing_profits:
#             return

#         self.solutions.append(copy.deepcopy(solution))

#         # Ταξινόμηση: καλύτερη πρώτη
#         self.solutions.sort(key=lambda s: s.total_profit, reverse=True)

#         # Κρατάμε μόνο τις max_size καλύτερες
#         if len(self.solutions) > self.max_size:
#             self.solutions.pop()

#     def get_random_target(self, current_sol=None):
#         """
#         Επιστρέφει τυχαία λύση από το elite set ως στόχο για Path Relinking.
#         Αποφεύγει να επιστρέψει λύση με ίδιο profit με την τρέχουσα.
#         """
#         candidates = self.solutions[:]

#         if current_sol is not None:
#             # Αφαίρεση λύσεων που μοιάζουν με την τρέχουσα
#             candidates = [s for s in candidates if s.total_profit != current_sol.total_profit]

#         if not candidates:
#             return None

#         return copy.deepcopy(random.choice(candidates))

#     def best(self):
#         """Επιστρέφει την καλύτερη λύση του elite set."""
#         if not self.solutions:
#             return None
#         return self.solutions[0]


# def path_relinking(model, start_sol, target_sol):
#     """
#     Path Relinking: εξερευνά το "μονοπάτι" μεταξύ δύο λύσεων.

#     Στρατηγική:
#     - Βρίσκει κόμβους που έχει ο target αλλά όχι η start (nodes_to_add)
#     - Σε κάθε βήμα, εισάγει τον πιο κερδοφόρο feasible κόμβο από τη λίστα
#     - Παρακολουθεί την καλύτερη λύση κατά μήκος του μονοπατιού

#     Επιστρέφει την καλύτερη λύση που βρέθηκε στο μονοπάτι.
#     """
#     sol      = copy.deepcopy(start_sol)
#     best_sol = copy.deepcopy(start_sol)

#     # Κόμβοι που έχει ο target αλλά όχι το start → θέλουμε να τους προσθέσουμε
#     nodes_to_add = target_sol.visited - sol.visited

#     while nodes_to_add:
#         best_node   = None
#         best_route  = None
#         best_pos    = None
#         best_delta  = None
#         best_profit = -float("inf")

#         # Βρίσκουμε ποιον κόμβο από τη λίστα αξίζει να προσθέσουμε
#         for node in nodes_to_add:
#             for route in sol.routes:
#                 for pos in range(1, len(route.nodes)):
#                     a = route.nodes[pos - 1]
#                     b = route.nodes[pos]

#                     # Επιπλέον χρόνος από εισαγωγή του κόμβου μεταξύ a και b
#                     delta = (
#                         model.cost_matrix[a][node]
#                         + model.cost_matrix[node][b]
#                         - model.cost_matrix[a][b]
#                     )

#                     # Έλεγχος χωρητικότητας
#                     if route.load + model.nodes[node].demand > model.capacity:
#                         continue

#                     # Έλεγχος χρόνου
#                     if route.time + delta > model.t_max:
#                         continue

#                     # Κρατάμε την πιο κερδοφόρα εισαγωγή
#                     if model.nodes[node].profit > best_profit:
#                         best_profit = model.nodes[node].profit
#                         best_node   = node
#                         best_route  = route
#                         best_pos    = pos
#                         best_delta  = delta

#         if best_node is None:
#             # Δεν μπορούμε να προσθέσουμε άλλους κόμβους — τερματισμός
#             break

#         # Εφαρμογή κίνησης
#         best_route.nodes.insert(best_pos, best_node)
#         best_route.load   += model.nodes[best_node].demand
#         best_route.time   += best_delta
#         best_route.profit += model.nodes[best_node].profit

#         sol.visited.add(best_node)
#         nodes_to_add.discard(best_node)

#         _update_metrics(sol)

#         # Παρακολούθηση καλύτερης λύσης κατά μήκος του μονοπατιού
#         if sol.total_profit > best_sol.total_profit:
#             best_sol = copy.deepcopy(sol)

#     return best_sol


# PathRelinking.py
import copy
import random


def _update_metrics(sol):
    """Ενημερώνει τα συνολικά metrics της λύσης."""
    sol.total_profit = sum(r.profit for r in sol.routes)
    sol.total_time   = sum(r.time   for r in sol.routes)
    sol.total_load   = sum(r.load   for r in sol.routes)


class EliteSet:
    """
    Κρατάει τις k καλύτερες λύσεις που βρέθηκαν κατά την αναζήτηση.

    Αν enforce_mandatory=True: γίνονται δεκτές ΜΟΝΟ λύσεις που περιέχουν
    όλους τους mandatory κόμβους — αποφυγή infeasible λύσεων στο elite set.
    """

    def __init__(self, model, max_size=5, enforce_mandatory=False):
        self.model             = model
        self.max_size          = max_size
        self.enforce_mandatory = enforce_mandatory
        self.solutions         = []

        # Προ-υπολογισμός mandatory IDs για γρήγορο έλεγχο
        self.mandatory_ids = {
            node.id
            for node in model.nodes
            if node.isMandatory
        }

    def _is_valid(self, solution):
        """
        Έλεγχος αν η λύση είναι αποδεκτή για το elite set.
        Αν enforce_mandatory: πρέπει να περιέχει όλους τους mandatory κόμβους.
        """
        if not self.enforce_mandatory:
            return True

        visited_in_routes = {
            node
            for route in solution.routes
            for node in route.nodes
            if node != 0
        }

        return self.mandatory_ids.issubset(visited_in_routes)

    def try_add(self, solution):
        """
        Προσπαθεί να εισάγει τη λύση στο elite set.
        Απορρίπτει: infeasible λύσεις (mandatory) και διπλότυπα profit.
        """
        if not self._is_valid(solution):
            return  # Infeasible ως προς mandatory — δεν εισάγεται

        existing_profits = {s.total_profit for s in self.solutions}
        if solution.total_profit in existing_profits:
            return  # Διπλότυπο — δεν εισάγεται

        self.solutions.append(copy.deepcopy(solution))
        self.solutions.sort(key=lambda s: s.total_profit, reverse=True)

        if len(self.solutions) > self.max_size:
            self.solutions.pop()  # Αφαίρεση της χειρότερης

    def get_random_target(self, current_sol=None):
        """
        Επιστρέφει τυχαία λύση από το elite set ως στόχο για Path Relinking.
        Αποφεύγει λύσεις με ίδιο profit με την τρέχουσα.
        """
        candidates = self.solutions[:]

        if current_sol is not None:
            candidates = [
                s for s in candidates
                if s.total_profit != current_sol.total_profit
            ]

        if not candidates:
            return None

        return copy.deepcopy(random.choice(candidates))

    def best(self):
        """Η καλύτερη λύση του elite set."""
        return self.solutions[0] if self.solutions else None


# ─────────────────────────────────────────────────────────────────────────────


def path_relinking(model, start_sol, target_sol, enforce_mandatory=False):
    """
    Path Relinking: εξερεύνηση του "μονοπατιού" μεταξύ δύο λύσεων.

    Στρατηγική:
      - Βρίσκει κόμβους που έχει ο target αλλά όχι η start (nodes_to_add)
      - Σε κάθε βήμα εισάγει τον πιο κερδοφόρο feasible κόμβο
      - Παρακολουθεί την καλύτερη λύση κατά μήκος του μονοπατιού

    Αν enforce_mandatory=True:
      - Mandatory κόμβοι εισάγονται ΠΡΩΤΑ (πριν τους optional)
      - Αν mandatory κόμβος δεν χωράει, δοκιμάζει "make room":
        αφαιρεί τον worst optional κόμβο για να κάνει χώρο
      - Ποτέ δεν αφαιρεί mandatory κόμβο κατά το make room

    Επιστρέφει την καλύτερη λύση που βρέθηκε κατά μήκος του μονοπατιού.
    """
    sol      = copy.deepcopy(start_sol)
    best_sol = copy.deepcopy(start_sol)

    # Κόμβοι που έχει ο target αλλά όχι το start
    nodes_to_add = target_sol.visited - sol.visited

    if enforce_mandatory:
        # Mandatory πρώτα, μετά optional κατά φθίνον κέρδος
        ordered_nodes = _sort_nodes_mandatory_first(model, nodes_to_add)
    else:
        # Απλή ταξινόμηση κατά φθίνον κέρδος
        ordered_nodes = sorted(nodes_to_add, key=lambda n: model.nodes[n].profit, reverse=True)

    for node in ordered_nodes:
        if node not in nodes_to_add:
            continue  # Μπορεί να έχει ήδη εισαχθεί έμμεσα

        # Προσπάθεια απευθείας εισαγωγής
        inserted = _try_direct_insert(model, sol, node)

        # Αν δεν χωράει και είναι mandatory: δοκιμή "make room"
        if not inserted and enforce_mandatory and model.nodes[node].isMandatory:
            inserted = _make_room_and_insert(model, sol, node)

        if inserted:
            nodes_to_add.discard(node)
            _update_metrics(sol)

            # Παρακολούθηση καλύτερης λύσης κατά μήκος του μονοπατιού
            if sol.total_profit > best_sol.total_profit:
                best_sol = copy.deepcopy(sol)

    return best_sol


# ─────────────────────────────────────────────────────────────────────────────
#  ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ
# ─────────────────────────────────────────────────────────────────────────────

def _sort_nodes_mandatory_first(model, node_set):
    """
    Ταξινομεί τους κόμβους ώστε οι mandatory να προηγούνται.
    Εντός κάθε ομάδας: φθίνουσα ταξινόμηση κατά κέρδος.
    """
    mandatory = sorted(
        [n for n in node_set if model.nodes[n].isMandatory],
        key=lambda n: model.nodes[n].profit,
        reverse=True
    )
    optional = sorted(
        [n for n in node_set if not model.nodes[n].isMandatory],
        key=lambda n: model.nodes[n].profit,
        reverse=True
    )
    return mandatory + optional


def _try_direct_insert(model, sol, node):
    """
    Δοκιμάζει να εισάγει τον κόμβο στη φτηνότερη feasible θέση
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
    Για κάθε route: αφαιρεί τον optional κόμβο με το χειρότερο
    profit/demand ratio και δοκιμάζει να εισάγει τον mandatory.

    Αν η εισαγωγή πετύχει → η αφαίρεση γίνεται μόνιμη.
    Αν όχι → rollback (επαναφορά του optional).

    Ποτέ δεν αφαιρεί mandatory κόμβο για να κάνει χώρο.

    Επιστρέφει True αν η εισαγωγή πέτυχε.
    """
    for route in sol.routes:

        # Εύρεση του worst optional στο route
        worst_pos   = None
        worst_score = float("inf")

        for pos in range(1, len(route.nodes) - 1):
            candidate = route.nodes[pos]

            # Ποτέ δεν αφαιρούμε mandatory για να κάνουμε χώρο σε άλλον
            if model.nodes[candidate].isMandatory:
                continue

            profit = model.nodes[candidate].profit
            demand = model.nodes[candidate].demand
            score  = profit / demand if demand > 0 else float(profit)

            if score < worst_score:
                worst_score = score
                worst_pos   = pos

        if worst_pos is None:
            continue  # Μόνο mandatory στο route — παράλειψη

        # Προσωρινή αφαίρεση του worst optional
        removed_node = route.nodes[worst_pos]
        prev_n       = route.nodes[worst_pos - 1]
        next_n       = route.nodes[worst_pos + 1]

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

        # Δοκιμή εισαγωγής mandatory στο τώρα ελεύθερο route
        inserted = _try_direct_insert(model, sol, mand_node)

        if inserted:
            return True  # Επιτυχία — ο removed_node παραμένει εκτός

        # Αποτυχία — rollback του removed_node
        route.nodes.insert(worst_pos, removed_node)
        route.load   += model.nodes[removed_node].demand
        route.time   += time_freed
        route.profit += model.nodes[removed_node].profit
        sol.visited.add(removed_node)

    return False