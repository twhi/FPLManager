from FPLManager.get_data import GetData
from FPLManager.opt import Wildcard
from FPLManager.opt import Substitution
from FPLManager.sim import Simulation
import pickle
import csv
import time

def save_to_pickle(variable, filename):
    with open(filename, 'wb') as handle:
        pickle.dump(variable, handle)

username = ''
password = ''

# 'sum_form_n': sum_form_n,
# 'sum_price_change_n': sum_price_change_n,
# 'sum_3_game_difficulty_n': sum_3_game_difficulty_n,
# 'sum_ict_index_n': sum_ict_index_n,
# 'sum_KPI_n': sum_KPI_n,
# 'sum_KPI_score': sum_KPI_score,
# 'total_cost': total_cost,
# 'total_score': total_score

processed_data = GetData(username, password, reduce=True, refresh=True).data

t0 = time.time()
# wc = Wildcard('KPI', processed_data, optimal_team=False)
sub = Substitution('KPI', processed_data, n_subs=4, optimal_team=False)
t1 = time.time()
print(t1-t0)

# todo, recommended lineup based on ep_next or KPI
# todo, players per team constraint not working