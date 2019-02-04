from FPLManager.get_data import GetData
import pickle
import requests
import json

def get_list(d, attribute):
    res = []
    for player in d:
        res.append(player[attribute])
    return res

def open_pickle(path_to_file):
    with open(path_to_file, 'rb') as handle:
        f = pickle.load(handle)
    return f

player_attributes = ['value_form', 'value_season', 'selected_by_percent', 'form', 'points_per_game', 'ep_this',
                         'ep_next', 'influence', 'creativity', 'threat', 'ict_index', 'price_change', 'price', 'KPI',
                         'now_cost', 'dreamteam_count', 'transfers_out', 'transfers_in', 'transfers_out_event',
                         'transfers_in_event', 'loans_in', 'loans_out', 'loaned_in', 'loaned_out',
                         'event_points', 'minutes', 'goals_scored', 'assists', 'clean_sheets', 'goals_conceded',
                         'own_goals', 'penalties_saved', 'penalties_missed', 'yellow_cards', 'red_cards', 'saves',
                         'bonus', 'bps', 'ea_index', '3_game_difficulty', 'form_n', 'price_change_n',
                         '3_game_difficulty_n', 'ict_index_n', 'KPI_n', 'score', 'KPI_score']

if __name__ == "__main__":

    username = 'tomw_121@hotmail.co.uk'
    password = ''
    master_table = open_pickle('./data/master_table.pickle')
    id_list = get_list(master_table, 'id')
    session = requests.Session()

    for p_id in id_list:
        u = 'https://fantasy.premierleague.com/drf/element-summary/{0}'.format(str(p_id))
        d = json.loads(session.get(u).text)['history']
        i = 0
        for gw in d:
            for attr in player_attributes:
                if attr in gw:
                    i += 1
                    value = gw[attr]
                    ended = True
            print(i)

    ender = True


