import csv
import time
from pathlib import Path
from icbs_complete import ICBS_Solver, sum_of_cost
from visualize import Animation

# Directory containing the instance files
instances_directory = Path("C:\\Users\\jagro\\Downloads\\MP ANuj\\MP ANuj\\Comparison\\")

# Get all files with a specific extension in the directory (e.g., .txt)
instance_files = list(instances_directory.glob("*.txt"))

def import_mapf_instance(filename):
    f = Path(filename)
    if not f.is_file():
        raise BaseException(filename + " does not exist.")
    f = open(filename, 'r')
    # first line: #rows #columns
    line = f.readline()
    rows, columns = [int(x) for x in line.split(' ')]
    rows = int(rows)
    columns = int(columns)
    # #rows lines with the map
    my_map = []
    for r in range(rows):
        line = f.readline()
        my_map.append([])
        for cell in line:
            if cell == '@':
                my_map[-1].append(True)
            elif cell == '.':
                my_map[-1].append(False)
    # #agents
    line = f.readline()
    num_agents = int(line)
    # #agents lines with the start/goal positions
    starts = []
    goals = []
    for a in range(num_agents):
        line = f.readline()
        sx, sy, gx, gy = [int(x) for x in line.split(' ')]
        starts.append((sx, sy))
        goals.append((gx, gy))
    f.close()
    return my_map, starts, goals

# Function to solve MAPF instance and gather information for both disjoint options
def solve_and_collect_info_for_both_disjoint(filename):
    my_map, starts, goals = import_mapf_instance(filename)
    results = []

    for disjoint_option in ["standard_splitting", "disjoint_splitting"]:
        cbs = ICBS_Solver(my_map, starts, goals)
        
        start_time = time.process_time()
        solution = cbs.find_solution(disjoint=disjoint_option, a_star_version="a_star")
        end_time = time.process_time()

        cpu_time = end_time - start_time

        if solution is not None:
            paths, nodes_gen, nodes_exp = solution[0], solution[1], solution[2]
            if paths is not None:
                cost = sum_of_cost(paths)
                results.append((nodes_gen, nodes_exp, cpu_time))
            else:
                results.append((0, 0, cpu_time))  # No solution
        else:
            results.append((0, 0, cpu_time))  # No solution

    return tuple(results)  # Return as tuple

# Run and collect information for each instance and both disjoint options
instance_info = []
for instance_path in instance_files:
    instance_info.append((instance_path,) + solve_and_collect_info_for_both_disjoint(instance_path))

# Save information to a CSV file
csv_filename = "C:\\Users\\jagro\\Downloads\\MP ANuj\\MP ANuj\\instance_info.csv"
with open(csv_filename, mode='w', newline='') as csv_file:
    fieldnames = ['Instance_File', 'Nodes_Generated_Standard', 'Nodes_Expanded_Standard',
                  'CPU_Time_Standard', 'Nodes_Generated_Disjoint', 'Nodes_Expanded_Disjoint',
                  'CPU_Time_Disjoint']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    for instance in instance_info:
        writer.writerow({
            'Instance_File': instance[0],
            'Nodes_Generated_Standard': instance[1][0],
            'Nodes_Expanded_Standard': instance[1][1],
            'CPU_Time_Standard': instance[1][2],
            'Nodes_Generated_Disjoint': instance[2][0],
            'Nodes_Expanded_Disjoint': instance[2][1],
            'CPU_Time_Disjoint': instance[2][2]
        })