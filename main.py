from analysis import Analysis
from fpl_data import FplData
from price_data import PriceData
from requests_session import RequestsSession
import csv

def trim_and_output_data(data):
    dict_filter = ['web_name', 'position', 'form', 'price', 'price_change', '3_game_difficulty', 'form_per_price']
    team_list = []
    for player in data:
        player_dict = dict((k, player[k]) for k in dict_filter if k in player)
        team_list.append(player_dict)

    keys = team_list[0].keys()
    with open('people.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(team_list)

if __name__ == "__main__":
    web = RequestsSession('', '') # username, password
    web.log_into_fpl()
    if web.login_status.status_code == 200:
        print('logged in successfully')
        f_data = FplData(web.session)
        p_data = PriceData(web)
        analysis = Analysis(web.session, f_data, p_data)
        trim_and_output_data(analysis.master_table)
        m_data = analysis.master_table

ender = True
