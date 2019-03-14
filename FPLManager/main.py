from FPLManager.get_data import GetData
from FPLManager.lineup import Lineup
from FPLManager.opt import Wildcard
from FPLManager.opt import Substitution


username = ''
password = ''
acc_id = 1255473

processed_data = GetData(username, password, acc_id, reduce=True, refresh=False).data


for p in processed_data.master_table:
    print(p['web_name'], p['KPI'], p['position'], sep=';')

# wc = Wildcard('price_change', processed_data, optimal_team=False)
# sub = Substitution('ep_next', processed_data, n_subs=4, optimal_team=False)
# lineup = Lineup(processed_data.team_list, param='ep_next').print_lineup()

# todo, identify players using name AND team in opt, this is causing incorrect players to be added to final squad

# todo generate optimum lineup for optimal squad after running simulation
ender = True

