from FPLManager.get_data import GetData
from FPLManager.lineup import Lineup
from FPLManager.opt import Wildcard
from FPLManager.opt import Substitution


username = ''
password = ''
acc_id = 1255473

processed_data = GetData(username, password, acc_id, reduce=True, refresh=True).data

wc = Wildcard('KPI', processed_data, optimal_team=False)
print('Wildcard simulation complete')
print('Best team/formation is as follows:')
lineup = Lineup(wc.squad, param='ep_next').print_lineup()

# sub = Substitution('KPI', processed_data, n_subs=1, optimal_team=False)
# print('\n###########################')
# print('\nSub simulation complete. Subs made:')
# for sub in sub.best_subs:
#     print(sub)
# print('\nBest team/formation is as follows:')
# lineup = Lineup(sub.best_team, param='ep_next').print_lineup()

ender = True

