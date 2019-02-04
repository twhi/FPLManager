from FPLManager.get_data import GetData
from FPLManager.opt import Optimise
from FPLManager.sim import Simulation



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


sim = Simulation(processed_data)
sim.find_n_replacements(2, ['Son'], False, 1000000, 'KPI_score')


# sim = Optimise('KPI', processed_data)
# print(sim.squad)

# opt_team_list = []
# for idx, attr in enumerate(player_attributes):
#     print('iteration ', idx, ' out of', len(player_attributes))
#     affordable_sim = Optimise(attr, processed_data, optimal_team=False)
#     optimal_sim = Optimise(attr, processed_data, optimal_team=True)
#     opt_team_list.append({
#         'opt_param': attr,
#         'afford_team': affordable_sim.squad,
#         'afford_score': 0,
#         'optimal_team': optimal_sim.squad,
#         'optimal_score': 0
#     })
#
# save_to_pickle(opt_team_list, './opt/gw24.pickle')

ender = True

# TODO - cache 3 game difficulty data so that process can be called during website updates