import random
import copy
from LocalSearch import _net_profit_global_exchange, local_search, _update_metrics


class ILS:
    def __init__(self, model, seed, enforce_mandatory=False):
        self.model             = model
        self.enforce_mandatory = enforce_mandatory
        random.seed(seed)

        self.mandatory_ids = {
            node.id for node in model.nodes if node.isMandatory
        }

    def _double_bridge_perturbation(self, solution):
        """
        Double Bridge perturbation

        Επιλέγει δύο routes τυχαία και ανταλλάσσει τμήματά τους.
        Αν το αποτέλεσμα παραβιάζει constraints, κάνει repair με
        αφαίρεση κόμβων που δεν χωράνε.

        Αυτή η κίνηση δεν μπορεί να γίνει από κανέναν local search operator
        — είναι "μακράς εμβέλειας" και γι' αυτό αποτελεσματική.
        """
        sol = copy.deepcopy(solution)

        # Επιλογή δύο routes με τουλάχιστον 3 κόμβους (εκτός depot)
        eligible = [r for r in sol.routes if len(r.nodes) > 3]

        if len(eligible) < 2:
            return sol  # Δεν υπάρχουν αρκετοί κόμβοι για perturbation

        r1, r2 = random.sample(eligible, 2)

        # Επιλογή τυχαίου σημείου κοπής για κάθε route
        # (εξαιρούμε τα depots στις θέσεις 0 και -1)
        cut1 = random.randint(1, len(r1.nodes) - 2)
        cut2 = random.randint(1, len(r2.nodes) - 2)

        # Ανταλλαγή ουρών: r1[:cut1] + r2[cut2:] και r2[:cut2] + r1[cut1:]
        new_nodes_r1 = r1.nodes[:cut1] + r2.nodes[cut2:]
        new_nodes_r2 = r2.nodes[:cut2] + r1.nodes[cut1:]

        # Εφαρμογή και repair (αφαίρεση infeasible κόμβων)
        self._apply_and_repair( r1, new_nodes_r1)
        self._apply_and_repair( r2, new_nodes_r2)

        # Ενημέρωση visited από τα routes
        sol.visited = {
            node
            for route in sol.routes
            for node in route.nodes
            if node != 0
        }

        _update_metrics(sol)
        return sol
    

    def _route_rebuild_perturbation(self, solution):
        """
        Επιλέγει το λιγότερο αποδοτικό route (profit/time),
        αφαιρεί τους optional κόμβους του, και το ξαναχτίζει
        χρησιμοποιώντας τους ελεύθερους + unvisited κόμβους.

        Γιατί είναι πιο έξυπνο από double bridge:
        - Στοχεύει το "αδύναμο" route αντί να αλλάζει τυχαία
        - Δίνει πλήρη ελευθερία ανασχεδιασμού ενός route
        - Οι freed κόμβοι μπορούν να επανεισαχθούν και αλλού
        """
        sol = copy.deepcopy(solution)

        # Επιλογή route με χειρότερο profit/time ratio
        # (λιγότερο αποδοτικό = υποψήφιο για ανασχεδιασμό)
        worst_route = min(
            sol.routes,
            key=lambda r: r.profit / max(r.time, 1)
        )

        # Διαχωρισμός κόμβων σε mandatory (παραμένουν) και optional (ελευθερώνονται)
        freed_nodes    = []
        kept_mandatory = []

        for node in worst_route.nodes[1:-1]:
            if self.enforce_mandatory and self.model.nodes[node].isMandatory:
                kept_mandatory.append(node)
            else:
                freed_nodes.append(node)
                sol.visited.discard(node)

        # Επαναφορά route: depot → mandatory → depot
        worst_route.nodes  = [0] + kept_mandatory + [0]
        worst_route.load   = sum(self.model.nodes[n].demand for n in kept_mandatory)
        worst_route.time   = sum(
            self.model.cost_matrix[worst_route.nodes[i]][worst_route.nodes[i+1]]
            for i in range(len(worst_route.nodes) - 1)
        )
        worst_route.profit = sum(self.model.nodes[n].profit for n in kept_mandatory)

        # Pool υποψηφίων: freed (από αδειασμένο route) + unvisited
        all_unvisited = set(range(1, self.model.num_nodes)) - sol.visited
        candidate_pool = list(set(freed_nodes) | all_unvisited)

        # Ταξινόμηση κατά φθίνον profit/demand (πιο αξιόλογοι πρώτοι)
        candidate_pool.sort(
            key=lambda n: self.model.nodes[n].profit / max(self.model.nodes[n].demand, 1),
            reverse=True
        )

        # Greedy reconstruction: εισαγωγή κόμβων στο αδειασμένο route
        for node in candidate_pool:
            if node in sol.visited:
                continue

            best_pos   = None
            best_delta = float("inf")

            for pos in range(1, len(worst_route.nodes)):
                a = worst_route.nodes[pos - 1]
                b = worst_route.nodes[pos]

                delta = (
                    self.model.cost_matrix[a][node]
                    + self.model.cost_matrix[node][b]
                    - self.model.cost_matrix[a][b]
                )

                if worst_route.load + self.model.nodes[node].demand > self.model.capacity:
                    continue
                if worst_route.time + delta > self.model.t_max:
                    continue

                if delta < best_delta:
                    best_delta = delta
                    best_pos   = pos

            if best_pos is not None:
                worst_route.nodes.insert(best_pos, node)
                worst_route.load   += self.model.nodes[node].demand
                worst_route.time   += best_delta
                worst_route.profit += self.model.nodes[node].profit
                sol.visited.add(node)

        # Freed κόμβοι που δε χωράνε στο rebuilt route:
        # δοκίμασε εισαγωγή στα υπόλοιπα routes
        still_unplaced = [n for n in freed_nodes if n not in sol.visited]
        for node in still_unplaced:
            for route in sol.routes:
                if route is worst_route:
                    continue
                for pos in range(1, len(route.nodes)):
                    a = route.nodes[pos - 1]
                    b = route.nodes[pos]
                    delta = (
                        self.model.cost_matrix[a][node]
                        + self.model.cost_matrix[node][b]
                        - self.model.cost_matrix[a][b]
                    )
                    if (route.load + self.model.nodes[node].demand <= self.model.capacity
                            and route.time + delta <= self.model.t_max):
                        route.nodes.insert(pos, node)
                        route.load   += self.model.nodes[node].demand
                        route.time   += delta
                        route.profit += self.model.nodes[node].profit
                        sol.visited.add(node)
                        break

        _update_metrics(sol)
        return sol
    

    def _apply_and_repair(self, route, new_nodes):
        """
        Κατασκευάζει έγκυρο route από τη νέα λίστα κόμβων.

        Αφαιρεί ΚΑΘΕ κόμβο που παραβιάζει capacity ή time — ακόμα και mandatory.
        Τους mandatory που δεν χωράνε τους αφήνουμε να τους εισάγει το
        local_search μετά (μέσω _force_insert_mandatory).
        """
        valid = [0]   # Route ξεκινά από depot
        load  = 0
        time  = 0     # Τρέχων χρόνος route (περιλαμβάνει επιστροφή στο depot)

        for node in new_nodes[1:-1]:
            if node == 0:
                continue  # Αγνόηση τυχαίων depot στη μέση

            a = valid[-1]

            # Χρόνος εισαγωγής μεταξύ τελευταίου κόμβου (a) και depot (0)
            delta = (
                self.model.cost_matrix[a][node]
                + self.model.cost_matrix[node][0]
                - self.model.cost_matrix[a][0]
            )

            new_load = load + self.model.nodes[node].demand
            new_time = time + delta

            if new_load <= self.model.capacity and new_time <= self.model.t_max:
                # Feasible: εισαγωγή κόμβου
                valid.append(node)
                load = new_load
                time = new_time
            # Infeasible (optional ή mandatory): παράλειψη
            # Mandatory που λείπουν → _force_insert_mandatory στο local_search

        valid.append(0)  # Τελικό depot

        route.nodes  = valid
        route.load   = load
        route.profit = sum(self.model.nodes[n].profit for n in valid if n != 0)
        # Επανυπολογισμός χρόνου από την τελική λίστα για ακρίβεια
        route.time   = sum(
            self.model.cost_matrix[valid[i]][valid[i + 1]]
            for i in range(len(valid) - 1)
        )



    def _is_mandatory_feasible(self, solution):
        """Ελέγχει αν ολοι οι mandatory κόμβοι βρίσκονται στη λύση."""
        visited_in_routes = {
            node
            for route in solution.routes
            for node in route.nodes
            if node != 0
        }
        return self.mandatory_ids.issubset(visited_in_routes)

    def _force_mandatory_aggressive(self, solution):
        """
        Aggressive έκδοση του force_insert: αφαιρεί έως 2 optional κόμβους
        ανά route για να χωρέσει mandatory κόμβος που δεν μπαίνει αλλιώς.
        Καλείται μόνο αν το κανονικό local_search δεν αρκεί.
        """
        sol = copy.deepcopy(solution)

        missing = [
            node_id for node_id in self.mandatory_ids
            if node_id not in {
                n for r in sol.routes for n in r.nodes if n != 0
            }
        ]

        for mand_node in missing:
            inserted = False

            #  απευθείας εισαγωγή
            for route in sol.routes:
                if route.load + self.model.nodes[mand_node].demand > self.model.capacity:
                    continue
                for pos in range(1, len(route.nodes)):
                    a = route.nodes[pos - 1]
                    b = route.nodes[pos]
                    delta = (
                        self.model.cost_matrix[a][mand_node]
                        + self.model.cost_matrix[mand_node][b]
                        - self.model.cost_matrix[a][b]
                    )
                    if route.time + delta <= self.model.t_max:
                        route.nodes.insert(pos, mand_node)
                        route.load   += self.model.nodes[mand_node].demand
                        route.time   += delta
                        route.profit += self.model.nodes[mand_node].profit
                        sol.visited.add(mand_node)
                        inserted = True
                        break
                if inserted:
                    break

            if inserted:
                continue

            #  αφαίρεση 1 ή 2 optional για να κάνουμε χώρο
            for n_remove in [1, 2]:
                if inserted:
                    break

                for route in sol.routes:
                    # Εύρεση των n_remove worst optional κόμβων
                    optional_positions = [
                        pos for pos in range(1, len(route.nodes) - 1)
                        if not self.model.nodes[route.nodes[pos]].isMandatory
                    ]

                    if len(optional_positions) < n_remove:
                        continue

                    # Ταξινόμηση κατά ανιούσα profit/demand (worst πρώτοι)
                    optional_positions.sort(
                        key=lambda p: (
                            self.model.nodes[route.nodes[p]].profit
                            / max(self.model.nodes[route.nodes[p]].demand, 1)
                        )
                    )

                    # Αφαίρεση των n_remove worst
                    removed = []
                    for p in sorted(optional_positions[:n_remove], reverse=True):
                        node = route.nodes[p]
                        prev = route.nodes[p - 1]
                        nxt  = route.nodes[p + 1]
                        tf = (
                            self.model.cost_matrix[prev][node]
                            + self.model.cost_matrix[node][nxt]
                            - self.model.cost_matrix[prev][nxt]
                        )
                        route.nodes.pop(p)
                        route.load   -= self.model.nodes[node].demand
                        route.time   -= tf
                        route.profit -= self.model.nodes[node].profit
                        sol.visited.discard(node)
                        removed.append((p, node, tf))

                    # Δοκιμή εισαγωγής mandatory
                    for pos in range(1, len(route.nodes)):
                        a = route.nodes[pos - 1]
                        b = route.nodes[pos]
                        delta = (
                            self.model.cost_matrix[a][mand_node]
                            + self.model.cost_matrix[mand_node][b]
                            - self.model.cost_matrix[a][b]
                        )
                        if (route.load + self.model.nodes[mand_node].demand <= self.model.capacity
                                and route.time + delta <= self.model.t_max):
                            route.nodes.insert(pos, mand_node)
                            route.load   += self.model.nodes[mand_node].demand
                            route.time   += delta
                            route.profit += self.model.nodes[mand_node].profit
                            sol.visited.add(mand_node)
                            inserted = True
                            break

                    if not inserted:
                        # Rollback
                        for p, node, tf in sorted(removed, key=lambda x: x[0]):
                            route.nodes.insert(p, node)
                            route.load   += self.model.nodes[node].demand
                            route.time   += tf
                            route.profit += self.model.nodes[node].profit
                            sol.visited.add(node)
                    else:
                        break

        _update_metrics(sol)
        return sol
    


    def run(self, initial_solution, iterations=100):
        curr_sol = copy.deepcopy(initial_solution)
        best_sol = copy.deepcopy(initial_solution)

        no_improve_count = 0

        for it in range(iterations):


            perturbed = self._double_bridge_perturbation(curr_sol) 
            ls_sol = local_search(
                self.model, perturbed,
                enforce_mandatory=self.enforce_mandatory,
                max_passes=3,
                apply_two_opt=False
            ) 

            
            perturbed = self._route_rebuild_perturbation(ls_sol) 
            ls_sol = local_search(
                self.model, perturbed,
                enforce_mandatory=self.enforce_mandatory,
                max_passes=3,
                apply_two_opt=False
            ) 

   

            if it % 15 == 0:
                
                ls_sol, nge_improved = _net_profit_global_exchange(
                    self.model, ls_sol,
                    enforce_mandatory=self.enforce_mandatory,
                    profit_threshold=None  # adaptive threshold
                )
                if nge_improved:
                    
                    # Μετά από NGE: insert_unvisited για να γεμίσει τυχόν κενό demand
                    ls_sol = local_search(
                        self.model, ls_sol,
                        enforce_mandatory=self.enforce_mandatory,
                        max_passes=1,
                        apply_two_opt=False
                    )


            # αν λείπουν mandatory μετά το local search,
            # δοκιμάζουμε aggressive repair πριν απορρίψουμε
            if self.enforce_mandatory and not self._is_mandatory_feasible(ls_sol):
                ls_sol = self._force_mandatory_aggressive(ls_sol)

            # Τελικός έλεγχος: αν ακόμα λείπουν mandatory, απόρριψη
            if self.enforce_mandatory and not self._is_mandatory_feasible(ls_sol):
                no_improve_count += 1
                continue

            # Greedy acceptance
            if ls_sol.total_profit > curr_sol.total_profit:
                curr_sol         = copy.deepcopy(ls_sol)
                no_improve_count = 0
            else:
                no_improve_count += 1

            if ls_sol.total_profit > best_sol.total_profit:
                best_sol = copy.deepcopy(ls_sol)


            # Restart από best αν κολλήσουμε
            if no_improve_count >= 50:
                curr_sol         = copy.deepcopy(best_sol)
                no_improve_count = 0

        # Τελικό  local search
        best_sol = local_search(
            self.model, best_sol,
            enforce_mandatory=self.enforce_mandatory,
            max_passes=1000,
            apply_two_opt=True
        )

        # εξασφάλιση mandatory feasibility πριν επιστροφή
        if self.enforce_mandatory and not self._is_mandatory_feasible(best_sol):
            best_sol = self._force_mandatory_aggressive(best_sol)

        
        return best_sol

