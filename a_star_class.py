import time as timer
import heapq
from itertools import product
import numpy as np
import copy

def move(loc, dir):
    directions = [(0, 0), (0, -1), (1, 0), (0, 1), (-1, 0)]
    return loc[0] + directions[dir][0], loc[1] + directions[dir][1]

def get_sum_of_cost(paths):
    rst = 0
    for path in paths:
        # print(path)
        rst += len(path) - 1
        if(len(path)>1):
            assert path[-1] != path[-2]
    return rst

def compute_heuristics(my_map, goal):
    # Use Dijkstra to build a shortest-path tree rooted at the goal location
    open_list = []
    closed_list = dict()
    root = {'loc': goal, 'cost': 0}
    heapq.heappush(open_list, (root['cost'], goal, root))
    closed_list[goal] = root
    while len(open_list) > 0:
        (cost, loc, curr) = heapq.heappop(open_list)
        for dir in range(1,5):
            child_loc = move(loc, dir)
            child_cost = cost + 1
            if child_loc[0] < 0 or child_loc[0] >= len(my_map) \
               or child_loc[1] < 0 or child_loc[1] >= len(my_map[0]):
               continue
            if my_map[child_loc[0]][child_loc[1]]:
                continue
            child = {'loc': child_loc, 'cost': child_cost}
            if child_loc in closed_list:
                existing_node = closed_list[child_loc]
                if existing_node['cost'] > child_cost:
                    closed_list[child_loc] = child
                    # open_list.delete((existing_node['cost'], existing_node['loc'], existing_node))
                    heapq.heappush(open_list, (child_cost, child_loc, child))
            else:
                closed_list[child_loc] = child
                heapq.heappush(open_list, (child_cost, child_loc, child))

    # build the heuristics table
    h_values = dict()
    for loc, node in closed_list.items():
        h_values[loc] = node['cost']
    return h_values

def get_location(path, time):
    if time < 0:
        return path[0]
    elif time < len(path):
        return path[time]
    else:
        return path[-1]  # wait at the goal location


def get_path(goal_node,meta_agent):
    path = []
    for i in range(len(meta_agent)):
        path.append([])
    curr = goal_node
    while curr is not None:
        for i in range(len(meta_agent)):
            path[i].append(curr['loc'][i])
        curr = curr['parent']
    for i in range(len(meta_agent)):
        path[i].reverse()
        assert path[i] is not None

        print(path[i])

        if len(path[i]) > 1: 
            # remove trailing duplicates
            while path[i][-1] == path[i][-2]:
                path[i].pop()
                print(path[i])
                if len(path[i]) <= 1:
                    break
            # assert path[i][-1] != path[i][-2] # no repeats at the end!!

    assert path is not None
    return path

class A_Star(object):

    def __init__(self,my_map,starts,goals,heuristics,agents,contraints):         
        self.my_map = my_map
        self.num_generated = 0
        self.num_expanded = 0
        self.CPU_time = 0
        self.open_list = []
        self.closed_list = dict()
        self.constraints = contraints # to be used to create c_table
        self.agents = agents

        # check if meta_agent is only a simple agent (from basic CBS)
        if not isinstance(agents, list):
            self.agents = [agents]
            # print(meta_agent)

            # add meta_agent keys to constraints
            for c in self.constraints:
                c['meta_agent'] = {c['agent']}

        self.starts = [starts[a] for a in self.agents]
        self.heuristics = [heuristics[a] for a in self.agents]
        self.goals = [goals[a] for a in self.agents]

        self.c_table = [] # constraint table
        self.max_constraints = np.zeros((len(self.agents),), dtype=int)

    def push_node(self, node):

        f_value = node['g_val'] + node['h_val']
        paths_left = node['reached_goal'].count(False)
        heapq.heappush(self.open_list, (f_value, node['h_val'], node['loc'], self.num_generated, node))
        self.num_generated += 1
        
    def pop_node(self):
        _,_,_, id, curr = heapq.heappop(self.open_list)
        self.num_expanded += 1
        return curr

    # return a table that constains the list of constraints of all agents for each time step. 
    def build_constraint_table(self, agent):
        # constraint_table = {}
        constraint_table = dict()
        if not self.constraints:
            return constraint_table
        for constraint in self.constraints:
            timestep = constraint['timestep']
            t_constraint = []
            if timestep in constraint_table:
                t_constraint = constraint_table[timestep]

            # positive constraint for agent
            if constraint['positive'] and constraint['agent'] == agent:
                
                # constraint_table[timestep].append(constraint)
                t_constraint.append(constraint)
                constraint_table[timestep] = t_constraint
            # and negative (external) constraint for agent
            elif not constraint['positive'] and constraint['agent'] == agent:
                # constraint_table[timestep].append(constraint)
                t_constraint.append(constraint)
                constraint_table[timestep] = t_constraint
                # enforce positive constraints from other agents (i.e. create neg constraint)
            elif constraint['positive']: 
                neg_constraint = copy.deepcopy(constraint)
                neg_constraint['agent'] = agent
                # if edge collision
                if len(constraint['loc']) == 2:
                    # switch traversal direction
                    prev_loc = constraint['loc'][1]
                    curr_loc = constraint['loc'][0]
                    neg_constraint['loc'] = [prev_loc, curr_loc]
                neg_constraint['positive'] = False
                # constraint_table[timestep].append(neg_constraint)
                t_constraint.append(neg_constraint)
                constraint_table[timestep] = t_constraint
        
        return constraint_table

    # returns if a move at timestep violates a "positive" or a "negative" constraint in c_table
    def constraint_violated(self, curr_loc, next_loc, timestep, c_table_agent, agent):

        if timestep not in c_table_agent:
            return None
        
        for constraint in c_table_agent[timestep]:
            
            if agent == constraint['agent']:
                # vertex constraint
                if len(constraint['loc']) == 1:
                    # positive constraint
                    if constraint['positive'] and next_loc != constraint['loc'][0]:
                        # print("time {} positive constraint : {}".format(timestep, constraint))
                        return constraint
                    # negative constraint
                    elif not constraint['positive'] and next_loc == constraint['loc'][0]:
                        # print("time {} negative constraint : {}".format(timestep, constraint))
                        return constraint
                # edge constraint
                else:
                    if constraint['positive'] and constraint['loc'] != [curr_loc, next_loc]:
                        # print("time {} positive constraint : {}".format(timestep, constraint))
                        return constraint
                    if not constraint['positive'] and constraint['loc'] == [curr_loc, next_loc]:
                        # print("time {} negative constraint : {}".format(timestep, constraint))
                        return constraint

        return None

    # returns whether an agent at goal node at current timestep will violate a constraint in next timesteps
    def future_constraint_violated(self, curr_loc, timestep, max_timestep, c_table_agent, agent):

        for t in range(timestep+1, max_timestep+1):
            if t not in c_table_agent:
                continue

            for constraint in c_table_agent[t]:
        
                if agent == constraint['agent']:
                    # vertex constraint
                    if len(constraint['loc']) == 1:
                        # positive constraint
                        if constraint['positive'] and curr_loc != constraint['loc'][0]:
                            return True
                        # negative constraint
                        elif not constraint['positive'] and curr_loc == constraint['loc'][0]:
                            return True
        return False

    def generate_child_nodes(self, curr):        
        children = []
        ma_dirs = product(list(range(5)), repeat=len(self.agents)) # directions for move() for each agent: 0, 1, 2, 3, 4
        
        for dirs in ma_dirs: 
            # print(dirs)
            invalid_move = False
            child_loc = []
            # move each agent for new timestep & check for (internal) conflicts with each other
            for i, a in enumerate(self.agents):           
                    aloc = move(curr['loc'][i], dirs[i])
                    # vertex collision; check for duplicates in child_loc
                    if aloc in child_loc:
                        invalid_move = True
                        # print("internal conflict")
                        break
                    child_loc.append(move(curr['loc'][i], dirs[i]))   

            if invalid_move:
                continue

            for i, a in enumerate(self.agents):   
                # edge collision: check for matching locs in curr_loc and child_loc between two agents
                for j, a in enumerate(self.agents):   
                    if i != j:
                        # print(ai, aj)
                        if child_loc[i] == curr['loc'][j] and child_loc[j] == curr['loc'][i]:
                            invalid_move = True             
            
            if invalid_move:
                continue

            # check map constraints and external constraints
            for i, a in enumerate(self.agents):  
                next_loc= child_loc[i]
                # agent out of map bounds
                if next_loc[0]<0 or next_loc[0]>=len(self.my_map) or next_loc[1]<0 or next_loc[1]>=len(self.my_map[0]):
                    invalid_move = True
                # agechild_locnt collison with map obstacle
                elif self.my_map[next_loc[0]][next_loc[1]]:
                    invalid_move = True
                # agent is constrained by a negative external constraint
                elif self.constraint_violated(curr['loc'][i],next_loc,curr['timestep']+1,self.c_table[i], self.agents[i]):
                    invalid_move = True
                if invalid_move:
                    break

            if invalid_move:
                continue

            # find h_values for current moves
            h_value = 0
            for i in range(len(self.agents)):
                    h_value += self.heuristics[i][child_loc[i]]

            h_test = sum([self.heuristics[i][child_loc[i]] for i in range(len(self.agents))])

            assert h_value == h_test

            # g_value = curr['g_val']+ curr['reached_goal'].count(False)
            num_moves = curr['reached_goal'].count(False)
            # print("(edge) cost (curr -> child) in a* tree == ", num_moves)

            g_value = curr['g_val'] + num_moves


            reached_goal = [False for i in range(len(self.agents))]
            # for i, a in enumerate(self.agents):
            #     # print(child_loc[i], goal_loc[i])
            #     # print(max_constraints[i], curr['timestep']+1)
                
            #     if child_loc[i] == self.goals[i] and (curr['timestep']+1 > self.max_constraints[i]):
            #         # print("agent ", a, 'has reached_goal at timestep ', curr['timestep'] + 1)
            #         # print (self.max_constraints[i])
            #         reached_goal[i] = True

            for i, a in enumerate(self.agents):
                
                if not reached_goal[i] and child_loc[i] == self.goals[i]:

                    if curr['timestep']+1 <= self.max_constraints[i]:
                        if not self.future_constraint_violated(child_loc[i], curr['timestep']+1, self.max_constraints[i] ,self.c_table[i], self.agents[i]):
                    # print("agent ", a, 'has found solution at timestep ', curr['timestep'] + 1)
                    # print ('MAX CONSTRIANT:', self.max_constraints[i])
                            reached_goal[i] = True
                            # self.max_constraints[i] differs for each node
                    else:
                        reached_goal[i] = True

            child = {'loc': child_loc,
                    'g_val': g_value, # number of new locs (cost) added
                    'h_val': h_value,
                    'parent': curr,
                    'timestep': curr['timestep']+1,
                    'reached_goal': copy.deepcopy(reached_goal)
                    } 

            # print(child)

            children.append(child)

        return children






















    def compare_nodes(self, n1, n2):
        """Return true is n1 is better than n2."""

        # print(n1['g_val'] + n1['h_val'])
        # print(n2['g_val'] + n2['h_val'])

        assert isinstance(n1['g_val'] + n1['h_val'], int)
        assert isinstance(n2['g_val'] + n2['h_val'], int)

        return n1['g_val'] + n1['h_val'] < n2['g_val'] + n2['h_val']






    def find_paths(self):

        self.start_time = timer.time()

        print("> build constraint table")

        for i, a in enumerate(self.agents):
            table_i = self.build_constraint_table(a)
            print(table_i)
            self.c_table.append(table_i)
            if table_i.keys():
                self.max_constraints[i] = max(table_i.keys())


        h_value = sum([self.heuristics[i][self.starts[i]] for i in range(len(self.agents))])

        # assert h_value == h_test

        root = {'loc': [self.starts[j] for j in range(len(self.agents))],
                # 'F_val' : h_value, # only consider children with f_val == F_val
                'g_val': 0, 
                'h_val': h_value, 
                'parent': None,
                'timestep': 0,
                'reached_goal': [False for i in range(len(self.agents))]
                }

        # check if any any agents are already at goal loc
        for i, a in enumerate(self.agents):
            if root['loc'][i] == self.goals[i]:

                if root['timestep'] <= self.max_constraints[i]:
                    if not self.future_constraint_violated(root['loc'][i], root['timestep'], self.max_constraints[i] ,self.c_table[i], self.agents[i]):
                        root['reached_goal'][i] = True

                        self.max_constraints[i] = 0


        self.push_node(root)
        self.closed_list[(tuple(root['loc']),root['timestep'])] = [root]

        while len(self.open_list) > 0:

            # if num_node_generated >= 30:
            #     return

            curr = self.pop_node()

            solution_found = all(curr['reached_goal'][i] for i in range(len(self.agents)))
            # print(curr['reached_goal'] )

            if solution_found:
                return get_path(curr,self.agents)


            children = self.generate_child_nodes(curr)

            for child in children:

                f_value = child['g_val'] + child['h_val']

                # if (tuple(child['loc']),child['timestep']) in self.closed_list:
                #     existing_node = self.closed_list[(tuple(child['loc']),child['timestep'])]
                #     if self.compare_nodes(child, existing_node):
                #         self.closed_list[(tuple(child['loc']),child['timestep'])] = child
                #         self.push_node(child)
                # else:
                #     # print('bye child ',child['loc'])
                #     self.closed_list[(tuple(child['loc']),child['timestep'])] = child
                #     self.push_node(child)

                if (tuple(child['loc']),child['timestep']) in self.closed_list:
                    existing = self.closed_list[(tuple(child['loc']),child['timestep'])]
                    # if child not in existing_nodes:
                    #     print("child not in existing closed list")
                    if (child['g_val'] + child['h_val'] < existing['g_val'] + existing['h_val']) and (child['g_val'] < existing['g_val']) and child['reached_goal'].count(False) <= existing['reached_goal'].count(False):
                        print("child is better than existing in closed list")
                        self.closed_list[(tuple(child['loc']),child['timestep'])] = child
                        self.push_node(child)
                else:
                    # print('bye child ',child['loc'])
                    self.closed_list[(tuple(child['loc']),child['timestep'])] = child
                    self.push_node(child)

                # if (tuple(child['loc']),child['timestep']) not in self.closed_list:
                #     # existing_node = self.closed_list[(tuple(child['loc']),child['timestep'])]
                #     # if compare_nodes(child, existing_node):
                #     self.closed_list[(tuple(child['loc']),child['timestep'])] = child
                #     # print('bye child ',child['loc'])
                #     self.push_node(child)

            # if (tuple(curr['loc']),curr['timestep']) not in self.closed_list:
            #     self.closed_list[(tuple(curr['loc']),curr['timestep'])] = curr

        print('no solution')

        # print("\nEND OF A*\n") # comment out if needed
        return None        
