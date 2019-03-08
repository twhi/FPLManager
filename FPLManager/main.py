from FPLManager.get_data import GetData
from FPLManager.lineup import Lineup
from FPLManager.opt import Wildcard
from FPLManager.opt import Substitution
import pickle

def save_to_pickle(variable, filename):
    with open(filename, 'wb') as handle:
        pickle.dump(variable, handle)

username = ''
password = ''
acc_id = 1255473

processed_data = GetData(username, password, acc_id, reduce=False, refresh=True).data
tester = True
# for i in processed_data.master_table:
#     print(i['web_name'], i['ep_this'], i['ep_next'], i['KPI'], i['event_points'], sep=';')

# TODO get selling_price from processed_data.team_info
# TODO duplicate names causing absolute misery, need to figure out how to handle these
    # could perhaps add a unique identifier for each player within process
# todo generate optimum lineup for optimal squad after running simulation
# todo if login fails then fall back on the squad id method


# wc = Wildcard('KPI', processed_data, optimal_team=False)
# sub = Substitution('KPI', processed_data, n_subs=1, optimal_team=False)
# print('Simulation complete. Results have been output to a CSV')

lineup = Lineup(processed_data.team_list, param='KPI').print_lineup()


