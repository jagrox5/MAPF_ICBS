from pathlib import Path
# Import relevant functions and classes from the original script
from icbs_complete import ICBS_Solver, sum_of_cost
from visualize import Animation

# Set the file path to your MAPF instance
instance_file_path = "C:\\Users\\jagro\\Downloads\\MP ANuj\\MP ANuj\\Comparison\\test_7.txt"
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

# Read the MAPF instance from the file
my_map, starts, goals = import_mapf_instance(instance_file_path)

# Initialize the ICBS solver
cbs = ICBS_Solver(my_map, starts, goals)

# Run the ICBS solver to find a solution
solution = cbs.find_solution(disjoint= "standard_splitting" ,a_star_version="a_star")
#solution = cbs.find_solution(disjoint= "disjoint_splitting" ,a_star_version="a_star")

if solution is not None:
    paths, nodes_gen, nodes_exp = solution[0], solution[1], solution[2]
    if paths is not None:
        # Calculate and print the sum of costs
        cost = sum_of_cost(paths)
        print("Sum of Costs:", cost)

        # Visualize the paths using Animation class
        animation = Animation(my_map, starts, goals, paths)
        animation.show()

        # You can also save the animation to a file if needed
        # animation.save("output.mp4", 1.0)

        # Print the number of generated and expanded nodes
        print("Nodes Generated:", nodes_gen)
        print("Nodes Expanded:", nodes_exp)
    else:
        print("No solutions")
else:
    print("No solutions")
