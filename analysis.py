import json


class Analysis:

    def __init__(self, session, fpl_data, price_data):
        self.session = session
        self.master_table = fpl_data.master_data
        self.available_money = fpl_data.account_data['bank']
        self.team_info = fpl_data.team_data
        self.player_price_data = price_data.player_price_data
        self.player_stats_data = price_data.player_stats_data

        self.get_game_difficulties()
        self.get_price_data()
        self.get_stats_data()
        self.get_player_position()
        self.calculate_form_per_price()
        self.normalise_values()
        self.team_list = self.get_team_list()
        self.reduce_data()
        self.give_current_team_indexes()

    def give_current_team_indexes(self):
        for idx, player in enumerate(self.team_list):
            player['index'] = idx

    def reduce_data(self):
        for idx, player in enumerate(self.master_table):
            if player['ict_index_n'] == 0:
                del self.master_table[idx]

    def normalise_values(self):
        attributes = ['form', 'price_change', '3_game_difficulty', 'ict_index', 'KPI']
        for atr in attributes:
            self.calculate_normalised_attribute(atr)

    def min_max_values(self, attribute):
        val_list = []
        for item in self.master_table:
            val_list.append(item[attribute])
        val_list_float = [float(i) for i in val_list]
        mm = {'min': float(min(val_list_float)), 'max': float(max(val_list_float))}
        return mm

    def calculate_normalised_attribute(self, attribute):
        form_min_max = self.min_max_values(attribute)
        for player in self.master_table:
            player[attribute + '_n'] = round((float(player[attribute]) - form_min_max['min']) / (form_min_max['max'] - form_min_max['min']), 2)


    def calculate_form_per_price(self):
        for player in self.master_table:
            player['form_per_price'] = round(float(player['form']) / float(player['price']), 2)

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
                    t_list.append(player)
                    break
        return t_list

    def get_price_data(self):
        for p in self.master_table:
            for player in self.player_price_data:
                if player[1] == p['web_name']:
                    p['price_change'] = player[14]
                    p['price'] = player[6]
                    break

    def get_stats_data(self):
        for p in self.master_table:
            for player in self.player_stats_data:
                if player[1] == p['web_name']:
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
        player_url_template = 'https://fantasy.premierleague.com/drf/element-summary/[PLAYER_ID]'
        difficulty_list = []
        for player_id in player_list:
            player_url = player_url_template.replace('[PLAYER_ID]', str(player_id))
            fixtures_data = json.loads(self.session.get(player_url).text)['fixtures']
            difficulty_list.append(self._get_n_game_average_difficulty(3, fixtures_data))
        game_difficulties = dict(zip(team_list, difficulty_list))

        # append the difficulty to the master table for each player
        for player in self.master_table:
            player['3_game_difficulty'] = game_difficulties[player['team_code']]

    @staticmethod
    def _get_n_game_average_difficulty(number_games, fixtures_data):
        sum_difficulty = 0
        for i in range(0, number_games):
            sum_difficulty += fixtures_data[i]['difficulty']
        return round(sum_difficulty / number_games, 1)
