# import random
# import copy
# import math
# from Destroy_operators import random_destroy, worst_destroy
# from RepairOperators import minimum_repair, greedy_repair, random_repair
# from LocalSearch import local_search

# class ALNS:
#     def __init__(self, model, seed):
#         self.model = model
#         random.seed(seed)

#         self.destroy_operators = [
#             random_destroy,
#             worst_destroy
#         ]
#         self.repair_operators = [
#             minimum_repair
#         ]

#         self.destroy_weights = []
#         self.repair_weights = []

#         self.destroy_scores = []
#         self.repair_scores = []

#         self.destroy_usage = []
#         self.repair_usage = []

#     def initial_weights(self):
#         self.destroy_weights = [1] * len(self.destroy_operators)
#         self.repair_weights = [1] * len(self.repair_operators)

#     def initial_scores(self):
#         self.destroy_scores = [0] * len(self.destroy_operators)
#         self.repair_scores = [0] * len(self.repair_operators)

#     def initial_usage(self):
#         self.destroy_usage = [0] * len(self.destroy_operators)
#         self.repair_usage = [0] * len(self.repair_operators)

#     def select_destroy_operator(self):
#         ind = random.choices(range(len(self.destroy_operators)), weights=self.destroy_weights)[0]
#         self.destroy_usage[ind] += 1
#         return self.destroy_operators[ind]

#     def select_repair_operator(self):
#         ind = random.choices(range(len(self.repair_operators)), weights=self.repair_weights)[0]
#         self.repair_usage[ind] += 1
#         return self.repair_operators[ind]

#     def update_destroy_weights(self):
#         for i in range(len(self.destroy_usage)):
#             if self.destroy_usage[i] == 0:
#                 continue
#             self.destroy_weights[i] = max(0.1, self.destroy_scores[i] / self.destroy_usage[i])

#     # def update_destroy_weights(self):

#     # reaction = 0.2

#     # for i in range(len(self.destroy_usage)):

#     #     if self.destroy_usage[i] == 0:
#     #         continue

#     #     score = self.destroy_scores[i] / self.destroy_usage[i]

#     #     self.destroy_weights[i] = (
#     #         (1 - reaction) * self.destroy_weights[i]
#     #         + reaction * score
#     #     )

#     def update_repair_weights(self):
#         for i in range(len(self.repair_usage)):
#             if self.repair_usage[i] == 0:
#                 continue
#             self.repair_weights[i] = max ( 0.1, self.repair_scores[i] / self.repair_usage[i])

    

#     def accept(self, curr_sol, candidate_sol, temperature):

#         delta = candidate_sol.total_profit - curr_sol.total_profit

#         if delta >= 0:
#             return True

#         probability = math.exp(delta / temperature)

#         return random.random() < probability
            


#     def run(self, initial_solution, interations=500):
        
#         #temperature = 0.05 * initial_solution.total_profit
#         temperature = 100
#         cooling = 0.9
#         inter = 0
#         curr_sol = copy.deepcopy(initial_solution)
#         best_sol = copy.deepcopy(initial_solution)
#         self.initial_weights()
#         while inter < interations:
#             if inter % 100 == 0:
#                 self.update_destroy_weights()
#                 self.update_repair_weights()

#                 self.initial_scores()
#                 self.initial_usage()
            
#             destroy_op = self.select_destroy_operator()
#             repair_op = self.select_repair_operator()
            

#             partial_sol, removed_nodes = destroy_op(self.model, curr_sol)
#             candidate_sol = repair_op(self.model, partial_sol, removed_nodes)
#             #candidate_sol = local_search(self.model, candidate_sol)

#             if self.accept(curr_sol, candidate_sol, temperature):
                
#                 if candidate_sol.total_profit > curr_sol.total_profit:
        
#                     if candidate_sol.total_profit > best_sol.total_profit:
#                         best_sol = copy.deepcopy(candidate_sol)
#                         self.destroy_scores[self.destroy_operators.index(destroy_op)] += 10
#                         self.repair_scores[self.repair_operators.index(repair_op)] += 10
#                     else:
#                         self.destroy_scores[self.destroy_operators.index(destroy_op)] += 5
#                         self.repair_scores[self.repair_operators.index(repair_op)] += 5                    
#                 else:
#                     self.destroy_scores[self.destroy_operators.index(destroy_op)] += 1
#                     self.repair_scores[self.repair_operators.index(repair_op)] += 1                    
                
#                 # self.update_destroy_weights()
#                 # self.update_repair_weights()
#                 curr_sol = copy.deepcopy(candidate_sol)
#             temperature *= cooling
#             print(f"inter: {inter}, best_sol={best_sol.total_profit}, curr_sol={curr_sol.total_profit}, candidate_sol={candidate_sol.total_profit}, temperature={temperature}")
#             inter += 1
#         return best_sol


# ALNS_mandatory.py
import random
import copy
import math

from Destroy_operators import random_destroy_mandatory, worst_destroy_mandatory
from RepairOperators    import minimum_repair
from LocalSearch        import local_search


class ALNS:
    """
    ALNS για το Mandatory CTOP.

    Διαφορές από την κανονική έκδοση:
      - Destroy operators: ποτέ δεν αφαιρούν mandatory κόμβους
      - Repair operator:   minimum_repair (εισάγει mandatory πρώτα)
      - Μετά από κάθε repair: επαλήθευση ότι η λύση παραμένει feasible
        ως προς το mandatory constraint — αν όχι, απορρίπτεται
    """

    def __init__(self, model, seed):
        self.model = model
        random.seed(seed)

        # Mandatory-aware destroy operators (δεν αγγίζουν mandatory κόμβους)
        self.destroy_operators = [
            random_destroy_mandatory,
            worst_destroy_mandatory
        ]

        # Repair με προτεραιότητα mandatory κόμβων
        self.repair_operators = [
            minimum_repair
        ]

        self.destroy_weights = []
        self.repair_weights  = []
        self.destroy_scores  = []
        self.repair_scores   = []
        self.destroy_usage   = []
        self.repair_usage    = []

    # ── Αρχικοποίηση ─────────────────────────────────────────────────────────

    def initial_weights(self):
        self.destroy_weights = [1.0] * len(self.destroy_operators)
        self.repair_weights  = [1.0] * len(self.repair_operators)

    def initial_scores(self):
        self.destroy_scores = [0] * len(self.destroy_operators)
        self.repair_scores  = [0] * len(self.repair_operators)

    def initial_usage(self):
        self.destroy_usage = [0] * len(self.destroy_operators)
        self.repair_usage  = [0] * len(self.repair_operators)

    # ── Επιλογή Operators ────────────────────────────────────────────────────

    def select_destroy_operator(self):
        """Επιλογή destroy operator βάσει βαρών. Επιστρέφει (operator, index)."""
        idx = random.choices(range(len(self.destroy_operators)), weights=self.destroy_weights)[0]
        self.destroy_usage[idx] += 1
        return self.destroy_operators[idx], idx

    def select_repair_operator(self):
        """Επιλογή repair operator βάσει βαρών. Επιστρέφει (operator, index)."""
        idx = random.choices(range(len(self.repair_operators)), weights=self.repair_weights)[0]
        self.repair_usage[idx] += 1
        return self.repair_operators[idx], idx

    # ── Ενημέρωση Βαρών ──────────────────────────────────────────────────────

    def update_weights(self):
        """
        Reaction-based weight update: διατηρεί μακροπρόθεσμη μνήμη.
        Νέο βάρος = (1 - r) * παλιό + r * (score / usage)
        """
        reaction = 0.2

        for i in range(len(self.destroy_operators)):
            if self.destroy_usage[i] == 0:
                continue
            score = self.destroy_scores[i] / self.destroy_usage[i]
            self.destroy_weights[i] = (
                (1 - reaction) * self.destroy_weights[i] + reaction * score
            )
            self.destroy_weights[i] = max(0.1, self.destroy_weights[i])

        for i in range(len(self.repair_operators)):
            if self.repair_usage[i] == 0:
                continue
            score = self.repair_scores[i] / self.repair_usage[i]
            self.repair_weights[i] = (
                (1 - reaction) * self.repair_weights[i] + reaction * score
            )
            self.repair_weights[i] = max(0.1, self.repair_weights[i])

    # ── Simulated Annealing ───────────────────────────────────────────────────

    def accept(self, curr_sol, candidate_sol, temperature):
        """
        Κριτήριο αποδοχής SA.
        Στο mandatory case: απορρίπτουμε λύσεις που δεν έχουν όλους τους mandatory.
        """
        # Απόρριψη infeasible λύσεων ως προς mandatory constraint
        if not self._is_mandatory_feasible(candidate_sol):
            return False

        delta = candidate_sol.total_profit - curr_sol.total_profit

        if delta >= 0:
            return True

        if temperature < 1e-10:
            return False

        probability = math.exp(delta / temperature)
        return random.random() < probability

    def _is_mandatory_feasible(self, solution):
        """
        Ελέγχει αν ΟΛΟΙ οι mandatory κόμβοι βρίσκονται στη λύση.
        Απαραίτητο safety check μετά από κάθε destroy/repair κύκλο.
        """
        mandatory_ids = {
            node.id
            for node in self.model.nodes
            if node.isMandatory
        }

        # Συλλογή όλων των επισκεφθέντων κόμβων από τα routes
        visited_in_routes = set()
        for route in solution.routes:
            for node in route.nodes:
                if node != 0:  # Εξαίρεση depot
                    visited_in_routes.add(node)

        # Όλοι οι mandatory πρέπει να βρίσκονται στα routes
        return mandatory_ids.issubset(visited_in_routes)

    # ── Κύριος Βρόχος ────────────────────────────────────────────────────────

    def run(self, initial_solution, iterations=500):
        """
        Κύριος βρόχος ALNS με Simulated Annealing για mandatory CTOP.

        Η αρχική λύση ΠΡΕΠΕΙ να έχει όλους τους mandatory κόμβους.
        Το _is_mandatory_feasible στο accept() εγγυάται ότι δεν χάνουμε
        ποτέ mandatory κόμβο κατά τη διάρκεια της αναζήτησης.
        """
        # Έλεγχος αρχικής λύσης
        if not self._is_mandatory_feasible(initial_solution):
            raise ValueError(
                "Η αρχική λύση δεν περιέχει όλους τους mandatory κόμβους. "
                "Χρησιμοποίησε solve_mandatory() για να παραχθεί έγκυρη αρχική λύση."
            )

        # Θερμοκρασία βασισμένη στο profit της αρχικής λύσης
        initial_temp = max(1.0, 0.05 * initial_solution.total_profit)

        # Cooling rate: η θερμοκρασία πέφτει στο 1% της αρχικής στο τέλος
        cooling = (0.01) ** (1.0 / iterations)

        temperature = initial_temp
        curr_sol    = copy.deepcopy(initial_solution)
        best_sol    = copy.deepcopy(initial_solution)

        self.initial_weights()
        self.initial_scores()
        self.initial_usage()

        for it in range(iterations):

            # Ενημέρωση βαρών κάθε 50 iterations
            if it > 0 and it % 50 == 0:
                self.update_weights()
                self.initial_scores()
                self.initial_usage()

            destroy_op, d_idx = self.select_destroy_operator()
            repair_op,  r_idx = self.select_repair_operator()

            # Destroy: αφαίρεση ΜΟΝΟ optional κόμβων
            partial_sol, removed_nodes = destroy_op(self.model, curr_sol)

            # Repair: εισαγωγή με προτεραιότητα mandatory
            candidate_sol = repair_op(self.model, partial_sol, removed_nodes)

            # Προαιρετικό: local search μετά repair (αποσχολιάστε για βελτίωση)
            # candidate_sol = local_search(self.model, candidate_sol, enforce_mandatory=True)

            if self.accept(curr_sol, candidate_sol, temperature):

                if candidate_sol.total_profit > best_sol.total_profit:
                    best_sol = copy.deepcopy(candidate_sol)
                    self.destroy_scores[d_idx] += 10
                    self.repair_scores[r_idx]  += 10
                elif candidate_sol.total_profit > curr_sol.total_profit:
                    self.destroy_scores[d_idx] += 5
                    self.repair_scores[r_idx]  += 5
                else:
                    self.destroy_scores[d_idx] += 1
                    self.repair_scores[r_idx]  += 1

                curr_sol = copy.deepcopy(candidate_sol)

            temperature *= cooling

            print(
                f"iter={it:4d} | best={best_sol.total_profit} "
                f"| curr={curr_sol.total_profit} "
                f"| cand={candidate_sol.total_profit} "
                f"| temp={temperature:.4f}"
            )

        return best_sol