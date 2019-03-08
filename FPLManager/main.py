from FPLManager.get_data import GetData
from FPLManager.lineup import Lineup
from FPLManager.opt import Wildcard
from FPLManager.opt import Substitution


username = ''
password = ''
acc_id = 1255473

processed_data = GetData(username, password, acc_id, reduce=False, refresh=False).data
wc = Wildcard('KPI', processed_data, optimal_team=False)
# sub = Substitution('KPI', processed_data, n_subs=1, optimal_team=False)
# lineup = Lineup(processed_data.team_list, param='ep_next').print_lineup()

# todo generate optimum lineup for optimal squad after running simulation
ender = True

