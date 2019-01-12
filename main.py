from analysis import Analysis
from fpl_data import FplData
from price_data import PriceData
from requests_session import RequestsSession
import random
import csv
import pprint
import pickle


def filter_list_by_position(data, position):
    outlist = []
    for player in data:
        if player['position'] == position:
            outlist.append(player)
    return outlist


def pick_players(num, dataset):
    data = dataset.copy()
    selected = 0
    player_list = []
    while selected < num:
        index = random.randrange(len(data))
        elem = data[index]
        del data[index]
        player_list.append(elem)
        selected += 1
    return player_list


def pick_team(gk, df, md, fw):
    goalkeepers = pick_players(2, gk)
    defenders = pick_players(5, df)
    midfielders = pick_players(5, md)
    forwards = pick_players(3, fw)
    team = goalkeepers + defenders + midfielders + forwards

    total_budget = f_data.account_data['bank'] + f_data.account_data['total_balance']
    total_price = sum_value(team, 'price')

    if total_price < total_budget:
        return team
    else:
        return False


def monte_carlo():
    main_data = m_data.copy()
    gk = filter_list_by_position(main_data, 'G')
    df = filter_list_by_position(main_data, 'D')
    md = filter_list_by_position(main_data, 'M')
    fw = filter_list_by_position(main_data, 'F')

    team_list = []
    print('starting monte carlo')
    for i in range(10000):
        final_team = pick_team(gk, df, md, fw)
        score = score_team(final_team)
        if final_team:
            team_list.append(final_team)
    return team_list


def sum_value(t, attribute):
    s = 0
    for player in t:
        s += float(player[attribute])
    return round(s, 2)


def max_key_value(data, attribute):
    # type - list of dicts
    val_list = []
    for item in data:
        try:
            val_list.append(item[attribute])
        except:
            return True
    return float(max(val_list))


def score_team(t):
    sum_form_n = sum_value(t, 'form_n')
    sum_price_change_n = sum_value(t, 'price_change_n')
    sum_3_game_difficulty_n = sum_value(t, '3_game_difficulty_n')
    sum_ict_index_n = sum_value(t, 'ict_index_n')
    total_score = round(sum_form_n + sum_price_change_n - sum_3_game_difficulty_n + sum_ict_index_n, 2)
    total_cost = sum_value(t, 'price')
    return {'sum_form_n': sum_form_n, 'sum_price_change_n': sum_price_change_n,
            'sum_3_game_difficulty_n': sum_3_game_difficulty_n, 'sum_ict_index_n': sum_ict_index_n,
            'total_cost': total_cost, 'total_score': total_score}


def find_replacements(num_replacements, current_team, balance, master_list):
    main_data = master_list.copy()
    main_data_s = remove_currently_owned_players(current_team, main_data)
    player_list = split_main_data_by_position(main_data_s)
    c_team_stats = score_team(current_team)
    max_iterations = 5000000
    new_team_list = find_replacement_players(balance, c_team_stats, current_team, max_iterations, num_replacements, player_list)
    return new_team_list


def find_replacement_players(balance, c_team_stats, current_team, max_iterations, num_replacements, player_list):
    new_team_list = []
    for i in range(max_iterations):

        # make a copy of current team to ensure that it isn't overwritten
        c_team = current_team.copy()
        n_team = current_team.copy()

        # make a copy of player_list
        p_list = {}
        for pos in player_list:
            p_list[pos] = player_list[pos].copy()

        # carry out replacements
        replacements = []
        for i in range(num_replacements):
            # choose random player to take out of squad
            index_old = random.randrange(len(c_team))
            player_out = c_team[index_old]
            del c_team[index_old]

            # choose random player to replace
            index_new = random.randrange(len(p_list[player_out['position']]))
            player_in = p_list[player_out['position']][index_new]
            del p_list[player_out['position']][index_new]

            # add new player to team list
            n_team[index_old] = player_in

            # create replacement object
            replacements.append({'old': player_out, 'new': player_in})

        # score new team
        n_team_stats = score_team(n_team)

        if n_team_stats['total_cost'] <= balance:
            if n_team_stats['sum_ict_index_n'] > c_team_stats['sum_ict_index_n']:
                if n_team_stats['sum_form_n'] > c_team_stats['sum_form_n']:
                    if n_team_stats['sum_3_game_difficulty_n'] < c_team_stats['sum_3_game_difficulty_n']:
                        if n_team_stats['sum_price_change_n'] > c_team_stats['sum_price_change_n']:
                            new_team_list.append({'team': n_team, 'stats': n_team_stats, 'replacements': replacements})
    return new_team_list


def split_main_data_by_position(main_data_s):
    # create position specific player dict
    gk = filter_list_by_position(main_data_s, 'G')
    df = filter_list_by_position(main_data_s, 'D')
    md = filter_list_by_position(main_data_s, 'M')
    fw = filter_list_by_position(main_data_s, 'F')
    player_list = {'G': gk, 'D': df, 'M': md, 'F': fw}
    return player_list


def remove_currently_owned_players(current_team, main_data):
    # remove players in current team from master list to ensure that a new player is selected every time
    team_name_list = [i['web_name'] for i in current_team]
    for idx, player in enumerate(main_data):
        if player['web_name'] in team_name_list:
            del main_data[idx]
    return main_data


def save_to_pickle(variable, filename):
    with open(filename + '.pickle', 'wb') as handle:
        pickle.dump(variable, handle)


def open_pickle(path_to_file):
    with open(path_to_file, 'rb') as handle:
        f = pickle.load(handle)
    return f


def output_top_n(team_list, current_team, order_by, num_teams):
    '''
    'order_by' parameters:
    'sum_form_n' - sum of the team's normalised form
    'sum_price_change_n' - sum of the team's normalised price change
    'sum_3_game_difficulty_n' - sum of the team's normalised game difficulty (higher = harder)
    'sum_ict_index_n' - sum of the team's ICT index (overall threat of the players)
    'total_score' - sum of the above
    '''

    # current team stats
    current_team_stats = score_team(current_team)

    # sort team list
    if order_by == 'sum_3_game_difficulty_n':
        team_list_sorted = sorted(team_list, key=lambda k: k['stats'][order_by])
    else:
        team_list_sorted = sorted(team_list, key=lambda k: k['stats'][order_by], reverse=True)

    # trim list to top 20 results
    if len(team_list_sorted) > num_teams:
        team_list_sorted = team_list_sorted[:num_teams]

    # prepare output variable
    output = []
    for idx, team in enumerate(team_list_sorted):
        # concatenate replace players into string
        replacements = ''
        for replacement in team['replacements']:
            replacements += replacement['old']['web_name'] + ' > ' + replacement['new']['web_name'] + '\n'

        full_team = ''
        for player in team['team']:
            full_team += player['web_name'] + ", "

        output.append({
            'replacements': replacements,
            'full team': full_team,
            'new team form': team['stats']['sum_form_n'],
            'new team ICT': team['stats']['sum_ict_index_n'],
            'new team price change': team['stats']['sum_price_change_n'],
            'new team 3 game difficulty': team['stats']['sum_3_game_difficulty_n'],
            'new team score': team['stats']['total_score'],
            'new team cost': team['stats']['total_cost'],
            'old team form': current_team_stats['sum_form_n'],
            'old team ICT': current_team_stats['sum_ict_index_n'],
            'old team price change': current_team_stats['sum_price_change_n'],
            'old team 3 game difficulty': current_team_stats['sum_3_game_difficulty_n'],
            'old team score': current_team_stats['total_score'],
            'old team cost': current_team_stats['total_cost'],
        })

    output_csv(output)


def output_csv(output):
    keys = output[0].keys()
    with open('output.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(output)


class Replacement:
    def __init__(self, fpl_data, analysed_data):
        self.f_data = fpl_data
        self.analysis = analysed_data
        self.total_balance = self.f_data.account_data['bank'] + self.f_data.account_data['total_balance']



if __name__ == "__main__":
    analysis = open_pickle("analysis.pickle")
    f_data = open_pickle("f_data.pickle")

    total_balance = f_data.account_data['bank'] + f_data.account_data['total_balance']

    t_list = find_replacements(4, analysis.team_list, total_balance, analysis.master_table)
    output_top_n(t_list, analysis.team_list, order_by='sum_ict_index_n', num_teams=100)
    ender = True

# if __name__ == "__main__":
#     web = RequestsSession('', '')  # username, password
#     web.log_into_fpl()
#     if web.login_status.status_code == 200:
#         print('logged in successfully')
#         f_data = FplData(web.session)
#         p_data = PriceData(web)
#         analysis = Analysis(web.session, f_data, p_data)