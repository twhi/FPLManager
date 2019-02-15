from FPLManager.get_data import GetData
from FPLManager.opt import Optimise
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

processed_data = GetData(username, password, reduce=True).data
# sim = Simulation(processed_data)
# squad = sim.find_n_replacements(num_replacements=3, max_iterations=5000000, order_by="total_score", num_teams=100, desired=[], outfield_only=False)

t0 = time.time()
sub = Substitution('KPI', processed_data, n_subs=1)
t1 = time.time()
print(t1-t0)