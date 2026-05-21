# import random
# import copy
# import math
# from Destroy_operators import random_destroy, worst_destroy
# from RepairOperators import greedy_repair, random_repair
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
#             greedy_repair,
#             random_repair
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
        
#         #temperature = 0.00001 * initial_solution.total_profit
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

# ALNS.py  (ίδια αλλαγή και για ALNS_mandatory.py)
import random
import copy
import math
from Destroy_operators import random_destroy, worst_destroy
from RepairOperators import greedy_repair, random_repair
from LocalSearch import local_search


class ALNS:
    def __init__(self, model, seed):
        self.model = model
        random.seed(seed)

        self.destroy_operators = [random_destroy, worst_destroy]
        self.repair_operators  = [greedy_repair, random_repair]

        self.destroy_weights = []
        self.repair_weights  = []
        self.destroy_scores  = []
        self.repair_scores   = []
        self.destroy_usage   = []
        self.repair_usage    = []

    def initial_weights(self):
        self.destroy_weights = [1.0] * len(self.destroy_operators)
        self.repair_weights  = [1.0] * len(self.repair_operators)

    def initial_scores(self):
        self.destroy_scores = [0] * len(self.destroy_operators)
        self.repair_scores  = [0] * len(self.repair_operators)

    def initial_usage(self):
        self.destroy_usage = [0] * len(self.destroy_operators)
        self.repair_usage  = [0] * len(self.repair_operators)

    def select_destroy_operator(self):
        """Επιλογή destroy operator βάσει βαρών — επιστρέφει (operator, index)."""
        idx = random.choices(range(len(self.destroy_operators)), weights=self.destroy_weights)[0]
        self.destroy_usage[idx] += 1
        return self.destroy_operators[idx], idx  # FIX: επιστρέφουμε και το index

    def select_repair_operator(self):
        """Επιλογή repair operator βάσει βαρών — επιστρέφει (operator, index)."""
        idx = random.choices(range(len(self.repair_operators)), weights=self.repair_weights)[0]
        self.repair_usage[idx] += 1
        return self.repair_operators[idx], idx  # FIX: επιστρέφουμε και το index

    def update_weights(self):
        """
        Reaction-based weight update:
        Νέο βάρος = (1 - r) * παλιό βάρος + r * (score / usage)
        Διατηρεί μακροπρόθεσμη μνήμη αντί να κάνει reset.
        """
        reaction = 0.2  # Πόσο γρήγορα αντιδρούν τα βάρη στις τελευταίες επιδόσεις

        for i in range(len(self.destroy_operators)):
            if self.destroy_usage[i] == 0:
                continue
            score = self.destroy_scores[i] / self.destroy_usage[i]
            self.destroy_weights[i] = (
                (1 - reaction) * self.destroy_weights[i] + reaction * score
            )
            # Ελάχιστο βάρος ώστε κανένας operator να μην αποκλειστεί εντελώς
            self.destroy_weights[i] = max(0.1, self.destroy_weights[i])

        for i in range(len(self.repair_operators)):
            if self.repair_usage[i] == 0:
                continue
            score = self.repair_scores[i] / self.repair_usage[i]
            self.repair_weights[i] = (
                (1 - reaction) * self.repair_weights[i] + reaction * score
            )
            self.repair_weights[i] = max(0.1, self.repair_weights[i])

    def accept(self, curr_sol, candidate_sol, temperature):
        """
        Κριτήριο αποδοχής Simulated Annealing.
        Πάντα αποδεχόμαστε βελτίωση.
        Χειρότερες λύσεις αποδεχόμαστε με πιθανότητα exp(delta / temperature).
        """
        delta = candidate_sol.total_profit - curr_sol.total_profit

        if delta >= 0:
            return True

        # Αποφυγή math domain error για πολύ χαμηλές θερμοκρασίες
        if temperature < 1e-10:
            return False

        probability = math.exp(delta / temperature)
        return random.random() < probability

    def run(self, initial_solution, iterations=500):
        """
        Κύριος βρόχος ALNS με Simulated Annealing.

        FIX θερμοκρασίας:
        - Αρχική θερμοκρασία βασισμένη στην κλίμακα του προβλήματος
        - Cooling rate υπολογισμένο ώστε η θερμοκρασία να φτάσει στο 1%
          της αρχικής τιμής στο τέλος των iterations (αντί να παγώσει στο 14%)
        """
        # Αρχική θερμοκρασία: αποδέχεται λύση χειρότερη κατά ~5% του αρχικού profit
        # με πιθανότητα ~80% (ευρετικό: ισορροπία εξερεύνησης/εκμετάλλευσης)
        initial_temp = max(1.0, 0.05 * initial_solution.total_profit)

        # FIX cooling: η θερμοκρασία να φτάσει στο 1% της αρχικής στο τέλος
        # final_temp = initial_temp * cooling^iterations  →  cooling = (0.01)^(1/iterations)
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

            # FIX: παίρνουμε και το index μαζί με τον operator
            destroy_op, d_idx = self.select_destroy_operator()
            repair_op,  r_idx = self.select_repair_operator()

            # Destroy: αφαίρεση κόμβων
            partial_sol, removed_nodes = destroy_op(self.model, curr_sol)

            # Repair: επανεισαγωγή κόμβων
            candidate_sol = repair_op(self.model, partial_sol, removed_nodes)

            # Προαιρετικό local search μετά το repair (αποσχολιάστε αν θέλετε)
            # candidate_sol = local_search(self.model, candidate_sol)

            if self.accept(curr_sol, candidate_sol, temperature):
                # Ενημέρωση scores βάσει ποιότητας αποτελέσματος
                if candidate_sol.total_profit > best_sol.total_profit:
                    # Νέα καλύτερη λύση — μέγιστη ανταμοιβή
                    best_sol = copy.deepcopy(candidate_sol)
                    self.destroy_scores[d_idx] += 10
                    self.repair_scores[r_idx]  += 10
                elif candidate_sol.total_profit > curr_sol.total_profit:
                    # Καλύτερη από την τρέχουσα, όχι από τη global best
                    self.destroy_scores[d_idx] += 5
                    self.repair_scores[r_idx]  += 5
                else:
                    # Αποδεκτή χειρότερη (SA acceptance) — μικρή ανταμοιβή
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