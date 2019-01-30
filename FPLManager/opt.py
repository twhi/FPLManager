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


def create_position_list(position):
    list_result = []
    for p in master_table:
        if p['position'] == position:
            list_result.append(1)
        else:
            list_result.append(0)
    return list_result


account_data = open_pickle('./opt/account_data.pickle')
master_table = open_pickle('./opt/master_table.pickle')
team_list = open_pickle('./opt/team_list.pickle')

gk_list = create_position_list('G')
df_list = create_position_list('D')
md_list = create_position_list('M')
fw_list = create_position_list('F')

# construct lists
players = []
kpi = []
price = []
for player in master_table:
    players.append(str(player['web_name']))
    kpi.append(round(float(player['price_change']), 2))
    price.append(float(player['price']))

maximum_price = account_data['bank'] + account_data['total_balance']
number_changes = 15

P = range(len(players))

# Declare problem instance, maximization problem
prob = LpProblem("Portfolio", LpMaximize)

# Declare decision variable x, which is 1 if a
# player is part of the squad and 0 else
x = LpVariable.matrix("x", list(P), 0, 1, LpInteger)

# Objective function -> Maximize votes
prob += sum(kpi[p] * x[p] for p in P)

# Constraint definition
prob += sum(price[p] * x[p] for p in P) <= (maximum_price + 100)  # total cost
prob += sum(gk_list[p] * x[p] for p in P) == 2  # number of goalies allowed
prob += sum(df_list[p] * x[p] for p in P) == 5  # number of defenders allowed
prob += sum(md_list[p] * x[p] for p in P) == 5  # number of midfielders allowed
prob += sum(fw_list[p] * x[p] for p in P) == 3  # number of forwards allowed

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
    print(player_data['web_name'], player_data['position'])
print('\n')
print('Total price - £' + str(total_price))
print('Total KPI - ' + str(total_kpi))

# TODO: rename the variables to something more appropriate so it makes sense when i revisit
# make this into a reusable class, so this can be called dynamically
