from analysis import Analysis
from fpl_data import FplData
from price_data import PriceData
from requests_session import RequestsSession
import random
import csv
import pprint


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
    total_cost = sum_value(t, 'price')
    return {'sum_form_n':sum_form_n, 'sum_price_change_n': sum_price_change_n, 'sum_3_game_difficulty_n': sum_3_game_difficulty_n, 'sum_ict_index_n': sum_ict_index_n, 'total_cost': total_cost}

def find_replacements(num_replacements, current_team, balance, master_list):
    # make a copy of main data to ensure that the main data list isn't overwritten
    main_data = master_list.copy()

    # create position specific player lists
    gk = filter_list_by_position(main_data, 'G')
    df = filter_list_by_position(main_data, 'D')
    md = filter_list_by_position(main_data, 'M')
    fw = filter_list_by_position(main_data, 'F')
    player_list = {'G': gk, 'D': df, 'M': md, 'F': fw}

    new_team_list = []

    # current team stats
    c_team_stats = score_team(current_team)

    print('searching for replacements')
    for i in range(10000):

        # make a copy of current team to ensure that it isn't overwritten
        c_team = current_team.copy()
        n_team = current_team.copy()

        # carry out replacements
        replacements = []
        for i in range(num_replacements):
            # choose random player to take out of squad
            index_old = random.randrange(len(c_team))
            player_out = c_team[index_old]

            # choose random player to replace
            index_new = random.randrange(len(player_list[player_out['position']]))
            player_in = player_list[player_out['position']][index_new]

            #
            n_team[index_old] = player_in
            replacements.append({'old': player_out, 'new': player_in})

        # new team stats
        n_team_stats = score_team(n_team)

        if n_team_stats['total_cost'] <= balance:
            if n_team_stats['sum_ict_index_n'] > c_team_stats['sum_ict_index_n']:
                new_team_list.append({'team':n_team, 'stats':n_team_stats, 'replacements': replacements})

    return new_team_list


if __name__ == "__main__":
    web = RequestsSession('', '')  # username, password
    web.log_into_fpl()
    if web.login_status.status_code == 200:
        print('logged in successfully')
        f_data = FplData(web.session)
        p_data = PriceData(web)
        analysis = Analysis(web.session, f_data, p_data)
        m_data = analysis.master_table
        total_balance = f_data.account_data['bank'] + f_data.account_data['total_balance']

        # remove players in current team from master list to ensure that a new player is selected every time
        team_name_list = [i['web_name'] for i in analysis.team_list]
        for idx, player in enumerate(m_data):
            if player['web_name'] in team_name_list:
                del m_data[idx]

        t_list = find_replacements(4, analysis.team_list, total_balance, m_data)

        ender = True

        # team_list = monte_carlo()
        #
        # keys = team_list[0].keys()
        # with open('output.csv', 'w', newline='') as output_file:
        #     dict_writer = csv.DictWriter(output_file, keys)
        #     dict_writer.writeheader()
        #     dict_writer.writerows(team_list)
        # ender = True
