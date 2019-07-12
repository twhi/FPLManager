import json
import requests

from FPLManager.caching import Caching
from FPLManager.fpl_data import FplData
from FPLManager.price_data import PriceData

class ProcessData(FplData, PriceData, Caching):

    def __init__(self, reduce_data, username_hash, **kwargs):

        if len(kwargs) == 1:
            self.username_hash = username_hash
            web = kwargs.get('web_session')
            self.session = web.session
            self.driver = web.driver
            FplData.__init__(self, web)
            PriceData.__init__(self, web)
            self.process_data()
            self.c_data()
        else:
            self.session = requests.Session()
            for (k, v) in kwargs.items():
                setattr(self, k, v)
            self.process_data()

        if reduce_data:
            self.reduce_data()

        if hasattr(self, 'driver'):
            self.driver.quit()

    def process_data(self):
        self.get_player_team_name()
        self.get_game_difficulties()
        self.get_price_data()
        self.get_stats_data()
        self.get_player_position()
        self.team_list = self.get_team_list()
        self.account_data['total_balance'] = sum(p['sell_price'] for p in self.team_list) + self.account_data['bank']
        self.add_selling_price()

    def add_selling_price(self):
        for p in self.master_table:
            if not 'sell_price' in p:
                p['sell_price'] = float(p['now_cost'] / 10)

    def get_player_team_name(self):
        for p in self.master_table:
            p['team_name'] = self.team_ids[p['team']]

    def c_data(self):
        Caching.__init__(self)
        self.cache_data(self.username_hash)

    def reduce_data(self):
        # remove player if not expected to score any points next week
        result = []
        for idx, player in enumerate(reversed(self.master_table)):
            if float(player['ep_next']) > 0.0:
                result.append(player)
                # print(player['web_name'], player['ep_next'], player['team_name'], sep=';')
        self.master_table = result

    def get_player_position(self):
        for player in self.master_table:
            if player['element_type'] == 1:
                player['position'] = 'G'
            elif player['element_type'] == 2:
                player['position'] = 'D'
            elif player['element_type'] == 3:
                player['position'] = 'M'
            elif player['element_type'] == 4:
                player['position'] = 'F'

    def get_team_list(self):
        t_list = []
        for p in self.team_info:
            for player in self.master_table:
                if p['element'] == player['id']:
                    player.update({'sell_price': p['selling_price'] / 10})
                    t_list.append(player)
                    break
        return t_list

    def get_price_data(self):
        for p in self.master_table:
            player_found = False
            for player in self.player_price_data:
                if player[1] == p['web_name'] and player[2] == p['team_name']:
                    p['price_change'] = player[14]
                    player_found = True
                    break
            # if the player isn't found then give them terrible attributes so that they're not accidentally used
            if not player_found:
                p['price_change'] = -3

    def get_stats_data(self):
        for p in self.master_table:
            for player in self.player_stats_data:
                if player[1] == p['web_name'] and player[2] == p['team_name']:
                    p['KPI'] = player[13]
                    break

    def get_game_difficulties(self):
        team_list = self.get_unique_team_ids()
        player_list = self.get_player_id_for_each_team(team_list)
        self.calculate_3_game_difficulty(player_list, team_list)

    def get_unique_team_ids(self):
        # get unique list of team ids
        team_list = []
        for item in self.master_table:
            team_list.append(item['team_code'])
        team_set = set(team_list)
        return list(team_set)

    def get_player_id_for_each_team(self, team_list):
        # for each team id find a player id
        player_list = []
        for team_id in team_list:
            for player in self.master_table:
                if player['team_code'] == team_id:
                    player_list.append(player['id'])
                    break
        return player_list

    def calculate_3_game_difficulty(self, player_list, team_list):
        # for each team get their average 3 game difficulty using each player's ID
        player_url_template = 'https://fantasy.premierleague.com/api/element-summary/[PLAYER_ID]/'
        difficulty_list = []
        gw_type_list = []
        for player_id in player_list:
            player_url = player_url_template.replace('[PLAYER_ID]', str(player_id))
            fixtures_data = json.loads(self.session.get(player_url).text)['fixtures']
            difficulty_list.append(self._get_n_game_average_difficulty(1, fixtures_data))
            gw_type_list.append(self.get_gw_type(self.account_data['next_event'], fixtures_data))
        game_difficulties = dict(zip(team_list, difficulty_list))
        game_types = dict(zip(team_list, gw_type_list))


        # append the difficulty to the master table for each player
        for player in self.master_table:
            player['3_game_difficulty'] = game_difficulties[player['team_code']]
            player['next_gameweek'] = game_types[player['team_code']]

    @staticmethod
    def get_gw_type(next_gw, fixtures):
        count_gw = sum(1 for f in fixtures if f['event'] == next_gw)
        if count_gw <= 2:
            return count_gw
        else:
            raise Exception('Number of games in a week shouldn\'t exceed 2. I counted {0}'.format(count_gw))

    @staticmethod
    def _get_n_game_average_difficulty(number_games, fixtures_data):
        sum_difficulty = 0
        for i in range(0, number_games):
            sum_difficulty += fixtures_data[i]['difficulty']
        return round(sum_difficulty / number_games, 1)
