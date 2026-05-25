import random
import copy
import math
from Destroy_operators import random_destroy, worst_destroy
from RepairOperators import greedy_repair, random_repair, regret_two_repair
from LocalSearch import local_search  # Εισαγωγή του local search

class ALNS:
    def __init__(self, model, seed):
        self.model = model
        random.seed(seed)

        self.destroy_operators = [random_destroy, worst_destroy]
        self.repair_operators  = [greedy_repair, random_repair, regret_two_repair]

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
        idx = random.choices(range(len(self.destroy_operators)), weights=self.destroy_weights)[0]
        self.destroy_usage[idx] += 1
        return self.destroy_operators[idx], idx

    def select_repair_operator(self):
        idx = random.choices(range(len(self.repair_operators)), weights=self.repair_weights)[0]
        self.repair_usage[idx] += 1
        return self.repair_operators[idx], idx

    def update_weights(self):
        reaction = 0.2
        for i in range(len(self.destroy_operators)):
            if self.destroy_usage[i] == 0:
                continue
            score = self.destroy_scores[i] / self.destroy_usage[i]
            self.destroy_weights[i] = (1 - reaction) * self.destroy_weights[i] + reaction * score
            self.destroy_weights[i] = max(0.1, self.destroy_weights[i])

        for i in range(len(self.repair_operators)):
            if self.repair_usage[i] == 0:
                continue
            score = self.repair_scores[i] / self.repair_usage[i]
            self.repair_weights[i] = (1 - reaction) * self.repair_weights[i] + reaction * score
            self.repair_weights[i] = max(0.1, self.repair_weights[i])

    def accept(self, curr_sol, candidate_sol, temperature):
        delta = candidate_sol.total_profit - curr_sol.total_profit

        # Αν η νέα λύση είναι καλύτερη, την αποδεχόμαστε πάντα
        if delta >= 0:
            return True

        if temperature < 1e-10:
            return False

        probability = math.exp(delta / temperature)
        return random.random() < probability

    def run(self, initial_solution, iterations=500):
        # Ρύθμιση αρχικής θερμοκρασίας ώστε να επιτρέπει αρχικό exploration
        initial_temp = max(10.0, 0.02 * initial_solution.total_profit)
        cooling = 0.01 ** (1.0 / iterations)

        temperature = initial_temp
        curr_sol    = copy.deepcopy(initial_solution)
        best_sol    = copy.deepcopy(initial_solution)

        self.initial_weights()
        self.initial_scores()
        self.initial_usage()

        for it in range(iterations):

            if it > 0 and it % 50 == 0:
                self.update_weights()
                self.initial_scores()
                self.initial_usage()

            destroy_op, d_idx = self.select_destroy_operator()
            repair_op,  r_idx = self.select_repair_operator()

            # 1. Καταστροφή (Αφαίρεση κόμβων)
            partial_sol, removed_nodes = destroy_op(self.model, curr_sol)

            # 2. Επιδιόρθωση (Επανεισαγωγή κόμβων)
            candidate_sol = repair_op(self.model, partial_sol, removed_nodes)

            # 🌟 ΚΡΙΣΙΜΟ FIX: Εφαρμογή Local Search στην candidate λύση 
            # για να "μαζέψει" τις κακές εισαγωγές του repair operator
            candidate_sol = local_search(self.model, candidate_sol)

            # 3. Έλεγχος Αποδοχής
            if self.accept(curr_sol, candidate_sol, temperature):
                if candidate_sol.total_profit > best_sol.total_profit:
                    best_sol = copy.deepcopy(candidate_sol)
                    self.destroy_scores[d_idx] += 12  # Μεγάλο bonus για global best
                    self.repair_scores[r_idx]  += 12
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
        #print weights
        print("Destroy Weights:", self.destroy_weights)
        print("Repair Weights:", self.repair_weights)

        return best_sol