from FPLManager.get_data import GetData
from FPLManager.opt import Optimise
from FPLManager.sim import Simulation
import pickle

def save_to_pickle(variable, filename):
    with open(filename, 'wb') as handle:
        pickle.dump(variable, handle)

username = ''
password = ''

processed_data = GetData(username, password).data

player_attributes = ['value_form', 'value_season', 'selected_by_percent', 'form', 'points_per_game', 'ep_this',
                     'ep_next', 'influence', 'creativity', 'threat', 'ict_index', 'price_change', 'price', 'KPI',
                     'now_cost', 'dreamteam_count', 'transfers_out', 'transfers_in', 'transfers_out_event',
                     'transfers_in_event', 'loans_in', 'loans_out', 'loaned_in', 'loaned_out', 'total_points',
                     'event_points', 'minutes', 'goals_scored', 'assists', 'clean_sheets', 'goals_conceded',
                     'own_goals', 'penalties_saved', 'penalties_missed', 'yellow_cards', 'red_cards', 'saves',
                     'bonus', 'bps', 'ea_index', '3_game_difficulty', 'form_n', 'price_change_n',
                     '3_game_difficulty_n', 'ict_index_n', 'KPI_n', 'score', 'KPI_score']


# sim = Simulation(processed_data)
# sim.find_n_replacements(num_replacements=2, desired=[], outfield_only=True, max_iterations=10000000, order_by='sum_KPI_score')


# sim = Optimise('3_game_difficulty', processed_data)
# print(sim.squad)

opt_team_list = []
for idx, attr in enumerate(player_attributes):
    print('iteration ', idx+1, ' out of', len(player_attributes))
    affordable_sim = Optimise(attr, processed_data, optimal_team=False)
    optimal_sim = Optimise(attr, processed_data, optimal_team=True)
    opt_team_list.append({
        'opt_param': attr,
        'afford_team': affordable_sim.squad,
        'afford_score': 0,
        'optimal_team': optimal_sim.squad,
        'optimal_score': 0
    })


player_round_points = {}
for player in processed_data.master_table:
    player_round_points[player['web_name']] = player['event_points']


for opt in opt_team_list:
    sum_val = 0
    for player in opt['afford_team']:
        sum_val += player_round_points[player]
    opt['afford_score'] = sum_val

    sum_val = 0
    for player in opt['optimal_team']:
        sum_val += player_round_points[player]
    opt['optimal_score'] = sum_val

save_to_pickle(opt_team_list, './opt/gw25.pickle')

ender = True

# TODO - cache 3 game difficulty data so that process can be called during website updates