from analysis import Analysis
from fpl_data import FplData
from price_data import PriceData
from requests_session import RequestsSession
import random
import csv
import pprint

if __name__ == "__main__":
    web = RequestsSession('', '')  # username, password
    web.log_into_fpl()
    if web.login_status.status_code == 200:
        print('logged in successfully')
        f_data = FplData(web.session)
        p_data = PriceData(web)
        analysis = Analysis(web.session, f_data, p_data)
        m_data = analysis.master_table


def filter_list_by_position(data, position):
    outlist = []
    for player in data:
        if player['position'] == position:
            outlist.append({'web_name': player['web_name'], 'price': player['price'], 'form': player['form'],
                            'price_change': player['price_change'], '3_game_difficulty': player['3_game_difficulty']})
    return outlist


def pick_team(gk, df, md, fw):
    goalkeepers = pick_players(2, gk)
    defenders = pick_players(5, df)
    midfielders = pick_players(5, md)
    forwards = pick_players(3, fw)
    team = goalkeepers + defenders + midfielders + forwards
    total_price = calculate_team_price(team)
    total_form = calculate_team_form(team)
    total_price_change = calculate_team_price_change(team)
    total_difficulty = calculate_total_difficulty(team)
    if total_price < 100:
        return {'team': team, 'price': total_price, 'form': total_form, 'price_change': total_price_change,
                '3_game_difficulty': total_difficulty}
    else:
        return False


def calculate_total_difficulty(t):
    diff = 0
    for player in t:
        diff += float(player['3_game_difficulty'])
    return diff


def calculate_team_price_change(t):
    pc = 0
    for player in t:
        pc += float(player['price_change'])
    return pc


def calculate_team_price(t):
    cost = 0
    for player in t:
        cost += float(player['price'])
    return cost


def calculate_team_form(t):
    form = 0
    for player in t:
        form += float(player['form'])
    return form


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
        if final_team:
            team_list.append(final_team)
    return team_list


def max_key_value(data, attribute):
    # type - list of dicts
    val_list = []
    for item in data:
       try:
           val_list.append(item[attribute])
       except:
           return True
    return float(max(val_list))

def postprocess(t_list):
    form_max = max_key_value(t_list, 'form')
    price_change_max = max_key_value(t_list, 'price_change')
    three_difficulty_max = max_key_value(t_list, '3_game_difficulty')

    final_list = []
    for team in t_list:
        team['form_norm'] = round(team['form'] / form_max, 1)
        team['pc_norm'] = round(team['price_change'] / price_change_max, 1)
        team['3diff_norm'] = round(team['3_game_difficulty'] / three_difficulty_max, 1)
        score = team['form_norm'] + team['pc_norm'] - team['3diff_norm']

        if team['form_norm'] > 0.8:
            final_list.append(team)


    return final_list

# team_list = monte_carlo()
# team_list = postprocess(team_list)
# keys = team_list[0].keys()
# with open('output.csv', 'w', newline='') as output_file:
#     dict_writer = csv.DictWriter(output_file, keys)
#     dict_writer.writeheader()
#     dict_writer.writerows(team_list)
# ender = True
