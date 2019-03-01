from FPLManager.get_data import GetData
from FPLManager.lineup import Lineup
from FPLManager.opt import Wildcard
from FPLManager.opt import Substitution
import pickle


def save_to_pickle(variable, filename):
    with open(filename, 'wb') as handle:
        pickle.dump(variable, handle)

username = 'twhitehead.1991@gmail.com'
password = 'password'

processed_data = GetData(username, password, reduce=True, refresh=True).data

# wc = Wildcard('KPI', processed_data, optimal_team=False)
# sub = Substitution('ep_next', processed_data, n_subs=2, optimal_team=False)
# print('Simulation complete. Results have been output to a CSV')

lineup = Lineup(processed_data.team_list, param='KPI').print_lineup()

# todo generate optimum lineup for optimal squad after running simulation
