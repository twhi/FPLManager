from FPLManager.get_data import GetData
from FPLManager.opt import Optimise
from FPLManager.opt import Substitution
from FPLManager.sim import Simulation
import pickle
import csv

def save_to_pickle(variable, filename):
    with open(filename, 'wb') as handle:
        pickle.dump(variable, handle)

username = ''
password = ''

player_attributes = ['value_form', 'value_season', 'selected_by_percent', 'form', 'points_per_game', 'ep_this',
                     'ep_next', 'influence', 'creativity', 'threat', 'ict_index', 'price_change', 'price', 'KPI',
                     'now_cost', 'dreamteam_count', 'transfers_out', 'transfers_in', 'transfers_out_event',
                     'transfers_in_event', 'loans_in', 'loans_out', 'loaned_in', 'loaned_out', 'total_points',
                     'event_points', 'minutes', 'goals_scored', 'assists', 'clean_sheets', 'goals_conceded',
                     'own_goals', 'penalties_saved', 'penalties_missed', 'yellow_cards', 'red_cards', 'saves',
                     'bonus', 'bps', 'ea_index', '3_game_difficulty', 'form_n', 'price_change_n',
                     '3_game_difficulty_n', 'ict_index_n', 'KPI_n', 'score', 'KPI_score']


processed_data = GetData(username, password, reduce=True).data


# opt_squad = Optimise('form', processed_data).squad
sub = Substitution('form', processed_data, n_subs=2)