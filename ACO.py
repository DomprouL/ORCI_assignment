# ACO.py
import random
import copy
from Solution import Route, Solution


def _update_metrics(sol):
    """Ενημερώνει τα συνολικά metrics της λύσης."""
    sol.total_profit = sum(r.profit for r in sol.routes)
    sol.total_time   = sum(r.time   for r in sol.routes)
    sol.total_load   = sum(r.load   for r in sol.routes)


class ACO:
    """
    Ant Colony Optimization για το Team Orienteering Problem.

    Κάθε μυρμήγκι κατασκευάζει μια πλήρη λύση (K διαδρομές).
    Επιλογή επόμενου κόμβου βασίζεται σε:
      - Φερομόνη τ(i,j)^alpha: μαθημένη εμπειρία από καλές λύσεις
      - Ευριστική η(i,j)^beta : profit_j / travel_time(i,j) — τοπική ελκτικότητα

    Μετά από κάθε iteration:
      - Εξάτμιση φερομόνης (evaporation)
      - Κατάθεση φερομόνης ανάλογη με κέρδος του καλύτερου μυρμηγκιού
    """

    def __init__(self, model, seed,
                 n_ants=20,
                 n_iterations=100,
                 alpha=1.0,   # Βάρος φερομόνης
                 beta=2.0,    # Βάρος ευριστικής
                 rho=0.1,     # Ρυθμός εξάτμισης (0 < rho < 1)
                 q0=0.7):     # Πιθανότητα εκμετάλλευσης vs εξερεύνησης

        self.model       = model
        self.n_ants      = n_ants
        self.n_iter      = n_iterations
        self.alpha       = alpha
        self.beta        = beta
        self.rho         = rho
        self.q0          = q0

        random.seed(seed)

        n = model.num_nodes

        # Αρχικοποίηση φερομόνης ομοιόμορφα σε όλες τις ακμές
        self.pheromone = [[1.0] * n for _ in range(n)]

        # Ελάχιστη φερομόνη: αποφυγή παγίδευσης σε τοπικό βέλτιστο
        self.tau_min = 0.01

    def _heuristic(self, from_node, to_node):
        """
        Ευριστική πληροφορία για κίνηση από from_node σε to_node.
        = κέρδος(to_node) / χρόνος_μετάβασης
        Υψηλό ratio = κόμβος με μεγάλο κέρδος κοντά μας → ελκτικός.
        """
        travel_time = self.model.cost_matrix[from_node][to_node]

        # Αποφυγή διαίρεσης με το μηδέν
        if travel_time < 1e-6:
            travel_time = 1e-6

        return self.model.nodes[to_node].profit / travel_time

    def _get_feasible_candidates(self, route, visited):
        """
        Επιστρέφει λίστα (node_id, delta_time) για κόμβους που μπορούν
        να εισαχθούν στο τέλος του route χωρίς παραβίαση περιορισμών.

        Το δέλτα υπολογίζεται ως: cost[last_node → new_node] + cost[new_node → depot]
                                  - cost[last_node → depot]
        (εισαγωγή πριν την τελική επιστροφή στο depot)
        """
        # Τελευταίος πραγματικός κόμβος (πριν την τελευταία επιστροφή στο depot)
        a = route.nodes[-2]
        b = 0  # Depot (τελευταίος κόμβος του route)

        candidates = []

        for node_id in range(1, self.model.num_nodes):
            # Παράλειψη ήδη επισκεφθέντων
            if node_id in visited:
                continue

            # Χρόνος εισαγωγής του node_id μεταξύ a και b
            delta = (
                self.model.cost_matrix[a][node_id]
                + self.model.cost_matrix[node_id][b]
                - self.model.cost_matrix[a][b]
            )

            # Έλεγχος περιορισμού χωρητικότητας
            if route.load + self.model.nodes[node_id].demand > self.model.capacity:
                continue

            # Έλεγχος περιορισμού χρόνου
            if route.time + delta > self.model.t_max:
                continue

            candidates.append((node_id, delta))

        return candidates

    def _select_next_node(self, current_node, candidates):
        """
        ACS rule για επιλογή επόμενου κόμβου:
        - Με πιθανότητα q0:    exploitation → επιλέγεται ο κόμβος με max(τ^α * η^β)
        - Με πιθανότητα 1-q0:  exploration  → roulette wheel βάσει τ^α * η^β

        Επιστρέφει (node_id, delta) ή (None, None).
        """
        if not candidates:
            return None, None

        # Υπολογισμός score για κάθε υποψήφιο
        scores = []
        for node_id, delta in candidates:
            tau = self.pheromone[current_node][node_id] ** self.alpha
            eta = self._heuristic(current_node, node_id) ** self.beta
            scores.append(tau * eta)

        if random.random() < self.q0:
            # Exploitation: επιλογή του καλύτερου
            best_idx = scores.index(max(scores))
            return candidates[best_idx]

        else:
            # Exploration: roulette wheel selection
            total = sum(scores)

            if total <= 0:
                return random.choice(candidates)

            threshold   = random.random() * total
            cumulative  = 0.0

            for (node_id, delta), score in zip(candidates, scores):
                cumulative += score
                if cumulative >= threshold:
                    return node_id, delta

            return candidates[-1]  # Fallback για floating point edge cases

    def _construct_ant_solution(self):
        """
        Ένα μυρμήγκι κατασκευάζει μια πλήρη λύση.
        Για κάθε όχημα: προσθέτει κόμβους έως ότου δεν υπάρχει feasible κόμβος.
        """
        routes  = [Route() for _ in range(self.model.vehicles)]
        visited = {0}  # Το depot θεωρείται πάντα επισκεφθέν

        for route in routes:
            while True:
                # Τρέχων τελευταίος κόμβος (πριν την επιστροφή στο depot)
                current_node = route.nodes[-2]

                # Εύρεση feasible υποψηφίων
                candidates = self._get_feasible_candidates(route, visited)

                if not candidates:
                    break  # Δεν χωράει άλλος κόμβος σε αυτό το route

                # Επιλογή επόμενου κόμβου
                next_node, delta = self._select_next_node(current_node, candidates)

                if next_node is None:
                    break

                # Εισαγωγή κόμβου πριν την τελευταία επιστροφή στο depot
                insert_pos = len(route.nodes) - 1
                route.nodes.insert(insert_pos, next_node)
                route.load   += self.model.nodes[next_node].demand
                route.time   += delta
                route.profit += self.model.nodes[next_node].profit

                visited.add(next_node)

        # Αφαίρεση depot από το visited set (το Solution.visited δεν περιλαμβάνει depot)
        visited.discard(0)

        solution = Solution(routes=routes, visited=visited)
        _update_metrics(solution)

        return solution

    def _evaporate_pheromone(self):
        """
        Εξάτμιση: μείωση όλης της φερομόνης κατά factor (1 - rho).
        Διατηρείται ελάχιστο tau_min για αποφυγή στασιμότητας.
        """
        for i in range(self.model.num_nodes):
            for j in range(self.model.num_nodes):
                self.pheromone[i][j] = max(
                    self.tau_min,
                    self.pheromone[i][j] * (1 - self.rho)
                )

    def _deposit_pheromone(self, solution):
        """
        Κατάθεση φερομόνης στις ακμές που χρησιμοποιήθηκαν.
        Καλύτερη λύση → περισσότερη φερομόνη → μεγαλύτερη επιρροή στο μέλλον.
        """
        deposit = float(solution.total_profit)  # Ποσό ανάλογο με κέρδος

        for route in solution.routes:
            for idx in range(len(route.nodes) - 1):
                a = route.nodes[idx]
                b = route.nodes[idx + 1]
                # Συμμετρική κατάθεση (undirected graph)
                self.pheromone[a][b] += deposit
                self.pheromone[b][a] += deposit

    def run(self, initial_solution=None):
        """
        Κύριος βρόχος ACO:
        1. Κάθε μυρμήγκι κατασκευάζει λύση
        2. Ενημέρωση φερομόνης (εξάτμιση + κατάθεση από το καλύτερο μυρμήγκι)
        3. Παρακολούθηση global best
        """
        # Αρχικοποίηση από δοθείσα λύση ή κατασκευή νέας
        if initial_solution is not None:
            best_sol = copy.deepcopy(initial_solution)
        else:
            best_sol = self._construct_ant_solution()

        print(f"\nACO Αρχή: best profit = {best_sol.total_profit}")

        for iteration in range(self.n_iter):
            ant_solutions = []

            # Κάθε μυρμήγκι κατασκευάζει ανεξάρτητα τη λύση του
            for _ in range(self.n_ants):
                sol = self._construct_ant_solution()
                ant_solutions.append(sol)

            # Καλύτερη λύση αυτής της iteration
            iter_best = max(ant_solutions, key=lambda s: s.total_profit)

            # Ενημέρωση φερομόνης: πρώτα εξάτμιση, μετά κατάθεση
            self._evaporate_pheromone()
            self._deposit_pheromone(iter_best)

            # Ενημέρωση global best
            if iter_best.total_profit > best_sol.total_profit:
                best_sol = copy.deepcopy(iter_best)

            print(
                f"ACO iter={iteration:3d} | "
                f"iter_best={iter_best.total_profit} | "
                f"global_best={best_sol.total_profit}"
            )

        return best_sol