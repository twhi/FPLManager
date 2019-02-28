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

processed_data = GetData(username, password, reduce=True, refresh=False).data

t0 = time.time()
# wc = Wildcard('team', processed_data, optimal_team=False)
sub = Substitution('ep_next', processed_data, n_subs=4, optimal_team=False)
t1 = time.time()
print(t1-t0)

# todo, recommended lineup based on ep_next or KPI