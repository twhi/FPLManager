from replace import Replacement
from requests_session import RequestsSession
from fpl_data import FplData
from price_data import PriceData
from analysis import Analysis
import random
import pickle


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


def max_key_value(data, attribute):
    # type - list of dicts
    val_list = []
    for item in data:
        try:
            val_list.append(item[attribute])
        except:
            return True
    return float(max(val_list))


def save_to_pickle(variable, filename):
    with open(filename + '.pickle', 'wb') as handle:
        pickle.dump(variable, handle)


def open_pickle(path_to_file):
    with open(path_to_file, 'rb') as handle:
        f = pickle.load(handle)
    return f


# if __name__ == "__main__":
#     analysis = open_pickle("analysis.pickle")
#     f_data = open_pickle("f_data.pickle")
# 
#     rep = Replacement(f_data, analysis)
#     rep.find_n_replacements(4, max_iterations=1000000, order_by="total_score", desired=['Salah'])

if __name__ == "__main__":
    username = ''
    password = ''

    if not username or not password:
        print('\nProcess failed. Incomplete credentials supplied.')
        exit()

    web = RequestsSession(username, password)  # username, password
    web.log_into_fpl()
    if web.login_status.status_code == 200:
        print('logged in successfully')
        f_data = FplData(web.session)
        p_data = PriceData(web)
        analysis = Analysis(web.session, f_data, p_data)
        save_to_pickle(f_data, "f_data")
        save_to_pickle(analysis, "analysis")
        rep = Replacement(f_data, analysis)
        rep.find_n_replacements(4, max_iterations=10000000, order_by="total_score", desired=['Salah'])
        # TODO: Next time, perhaps remove the goal keepers from the simulation, it seems to always suggest goalies and i don't really care for them
        # Could this be done by removing the 'G' bin from the position index method from the replace class?
