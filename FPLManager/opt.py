import pickle
from pulp import *

def open_pickle(path_to_file):
    with open(path_to_file, 'rb') as handle:
        f = pickle.load(handle)
    return f

def lookup_player_by_web_name(web_name):
    for p in master_table:
        if p['web_name'] == web_name:
            return p

account_data = open_pickle('./opt/account_data.pickle')
master_table = open_pickle('./opt/master_table.pickle')
team_list = open_pickle('./opt/team_list.pickle')

players = []
kpi = []
price = []
for player in master_table:
    players.append(str(player['web_name']))
    kpi.append(float(player['KPI']))
    price.append(float(player['price']))

maximum_price = account_data['bank'] + account_data['total_balance']
number_changes = 15

P = range(len(players))

# Declare problem instance, maximization problem
prob = LpProblem("Portfolio", LpMaximize) #LpMaximize

# Declare decision variable x, which is 1 if a
# player is part of the portfolio and 0 else
x = LpVariable.matrix("x", list(P), 0, 1, LpInteger)

# Objective function -> Maximize votes
prob += sum(kpi[p] * x[p] for p in P)

# Constraint definition
prob += sum(x[p] for p in P) == number_changes
prob += sum(price[p] * x[p] for p in P) <= maximum_price

# Start solving the problem instance
prob.solve()

# Extract solution
portfolio = [players[p] for p in P if x[p].varValue]

total_price = 0
total_kpi = 0
for player in portfolio:
    player_data = lookup_player_by_web_name(player)
    total_price += float(player_data['price'])
    total_kpi += float(player_data['KPI'])
    print(player_data['web_name'], player_data['price'], player_data['KPI'])
print('\n')
print('Total price - £' + str(total_price))
print('Total KPI - ' + str(total_kpi))

# TODO: adapt the solution based on this tutorial https://pythonhosted.org/PuLP/CaseStudies/a_blending_problem.html
# TODO: rename the variables to something more appropriate so it makes sense when i revisit
# TODO: optimise either score or kpi_score, kpi alone is pretty weak