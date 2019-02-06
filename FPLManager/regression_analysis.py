from FPLManager.get_data import GetData
import pickle
import requests
import json
import pandas as pd


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
                         'no'
                         ''
                         'w_cost', 'dreamteam_count', 'transfers_out', 'transfers_in', 'transfers_out_event',
                         'transfers_in_event', 'loans_in', 'loans_out', 'loaned_in', 'loaned_out',
                         'event_points', 'minutes', 'goals_scored', 'assists', 'clean_sheets', 'goals_conceded',
                         'own_goals', 'penalties_saved', 'penalties_missed', 'yellow_cards', 'red_cards', 'saves',
                         'bonus', 'bps', 'ea_index', '3_game_difficulty', 'form_n', 'price_change_n',
                         '3_game_difficulty_n', 'ict_index_n', 'KPI_n', 'score', 'KPI_score']


def save_to_pickle(variable, filename):
    with open(filename, 'wb') as handle:
        pickle.dump(variable, handle)

def get_historic_data(p_id_l):
    historic_data = []
    for idx, p_id in enumerate(p_id_l):
        print('player', idx + 1, 'out of', len(p_id_l))
        url = 'https://fantasy.premierleague.com/drf/element-summary/{0}'.format(str(p_id))
        player_data = json.loads(session.get(url).text)['history']
        historic_data.append(player_data)
    return historic_data


if __name__ == "__main__":

    username = 'tomw_121@hotmail.co.uk'
    password = ''

    p_data = GetData(username, password, reduce=False)
    p_id_list = get_list(p_data.data.master_table, 'id')

    exclude_list = ['kickoff_time', 'kickoff_time_formatted', 'was_home', 'total_points', 'id']
    convert_list = ['influence', 'creativity', 'threat', 'ict_index']

    h_data = open_pickle('./data/historic_data.pickle')

    # initialise out_dict
    out_dict = {}

    # prepopulate out_dict with keys
    test_set = h_data[0][0]
    for attr in test_set:
        if not attr in exclude_list:
            out_dict[attr] = []

    # add all data to out_dict
    for player in h_data:
        final_gw = True
        for gw in reversed(player):

            if not final_gw:
                for attr in gw:
                    if attr in convert_list:
                        gw[attr] = float(gw[attr])

                    if not attr in exclude_list:
                        out_dict[attr].append({attr:gw[attr], 'next_week_pts': points_obtained})

            points_obtained = gw['total_points']
            final_gw = False

    result = pd.DataFrame()
    for attr in out_dict:
        df_new = pd.DataFrame(out_dict[attr], columns=[attr, 'next_week_pts'])
        result = pd.concat([result, df_new], axis=1)

    # todo run linear regression on these data sets
    # todo perhaps run multiple linear regression for all attributes that contribute positively towards score

    result.to_csv('text.csv')
    ender = True


