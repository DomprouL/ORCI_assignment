def write_solution_to_file(solution, file_name):
        # Write the solution to a file in the specified format
        with open(file_name, "w") as f:
            for route in solution.routes:
                if route:
                    f.write(" ".join(map(str, route)) + "\n")

# Gets a list of nodes, Calculates the total utilization of each node (profit/demand) and returns a list of node IDs sorted by utilization in descending order
# If enforce_mandatory is True, mandatory nodes will be prioritized in the utilization list regardless of their profit/demand ratio
def calculate_utilization (nodes, enforce_mandatory=True):
    if enforce_mandatory:
        node_utilization = []
        mandatory_nodes = []
        optional_nodes = []
        for node in nodes:
            if node.demand > 0:
                utilization = node.profit / node.demand
                
                if node.isMandatory:
                    mandatory_nodes.append((node.id, utilization))
                else:
                    optional_nodes.append((node.id, utilization))
        

        # Sort mandatory nodes by profit/demand ratio
        mandatory_nodes_sorted = (node_id for node_id, _ in sorted(mandatory_nodes, key=lambda x: x[1], reverse=True))
        # Sort optional nodes by profit/demand ratio
        optional_nodes_sorted = (node_id for node_id, _ in sorted(optional_nodes, key=lambda x: x[1], reverse=True))

        # Combine mandatory and optional nodes, with mandatory nodes first
        sorted_nodes = list(mandatory_nodes_sorted) + list(optional_nodes_sorted)
    else:
        node_utilization = []
        for node in nodes:
            if node.demand > 0:
                node_utilization.append((node.id, node.profit / node.demand))
        sorted_nodes = [node_id for node_id, _ in sorted(node_utilization, key=lambda x: x[1], reverse=True)]
    # Return the sorted list of node IDs based on utilization
    return sorted_nodes