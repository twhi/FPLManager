import csv
import random
import uuid

def filter_list_by_position(data, position):
    """
    :param data: List of player dictionaries
    :param position: Player position code, either 'G', 'D', 'M' or 'F'
    :return:
    """
    outlist = []
    for player in data:
        if player['position'] == position:
            outlist.append(player)
    return outlist


def generate_csv(output):
    """
    :param output: A list of dicts

    Will output a csv named output.csv
    """
    keys = output[0].keys()
    unique_filename = str(uuid.uuid4())
    with open('./output_data/' + unique_filename + '.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(output)


def sum_value(t, attribute):
    """
    :param t: A list of player dictionaries
    :param attribute: The attribute that you want to sum
    :return: The sum of the specified attribute, rounded to 2 d.p
    """
    s = 0
    for player in t:
        s += float(player[attribute])
    return round(s, 2)


class Simulation:
    def __init__(self, analysed_data):
        self.total_balance = analysed_data.total_balance
        self.current_team = analysed_data.team_list
        self.master_table = analysed_data.master_table
        self.current_team_stats = self.score_team(self.current_team)
        self.outfield_only = None
        self.position_indicies = None
        self.num_replacements = None
        self.desired = None
        self.outfield_only = None
        self.max_iterations = None
        self.order_by = None
        self.num_teams = None
        self.team_list = None
        self.c_team = None
        self.n_team = None
        self.p_list = None
        self.p_indicies = None
        self.replacements = None
        self.n_team_stats = None


    def wildcard_squad(self, max_iterations=100000, order_by="total_score", desired=[], num_teams=100):
        print('Starting a Wildcard Squad Generator simulation...')
        self.desired = desired
        self.max_iterations = max_iterations
        self.order_by = order_by
        self.num_teams = num_teams

        self.player_list = self._split_main_data_by_position(self.master_table)
        self.player_index_lookup = self.generate_player_names_index_dict()

        self._get_position_indexes()

        self.start_wildcard_simulation()

        if len(self.team_list) > 0:
            self.output_data2()
        else:
            print('\nNo team improvements found for given input paramters. Sorry m8.')

    def start_wildcard_simulation(self):
        self.team_list = []
        for i in range(self.max_iterations):
            self.n_team = []
            for i in range(15):
                self.n_team.append('')

            self._copy_variables_for_wildcard()

            # do desired players
            for player in self.desired:
                player_info = self.player_index_lookup[player]
                player_in = self.p_list[player_info['position']][player_info['index']]  # get desired player from p_list
                del self.p_list[player_info['position']][player_info['index']]  # delete desired player from p_list

                idx = random.randrange(len(self.p_indicies[player_info['position']]))  # select a random index from the desired player's postion
                index_old = self.p_indicies[player_info['position']][idx]  # convert this to a player index
                del self.p_indicies[player_info['position']][idx]  # remove the selected index from the list so it can't be selected again
                if len(self.p_indicies[player_info['position']]) == 0:
                    del self.p_indicies[player_info['position']]

                self.n_team[index_old] = player_in

            # do random players
            for j in range(15 - len(self.desired)):
                pos_idx = random.choice(list(self.p_indicies.keys()))  # choose a random position to replace
                idx = random.randrange(len(self.p_indicies[pos_idx]))  # choose a random player from that position
                index_old = self.p_indicies[pos_idx][idx]
                del self.p_indicies[pos_idx][idx]  # remove the selected index from the list so it can't be selected again
                if len(self.p_indicies[pos_idx]) == 0:  # if the position index is empty then remove it to prevent it being randomly selected
                    del self.p_indicies[pos_idx]

                index_new = random.randrange(len(self.p_list[pos_idx]))  # choose random player to replace
                player_in = self.p_list[pos_idx][index_new]
                del self.p_list[pos_idx][index_new]
                self.n_team[index_old] = player_in

                # needs work, not quite working

            self.n_team_stats = self.score_team(self.n_team)
            self._bad_team_filter2()


    def _bad_team_filter2(self):
        # only keep simulated team if it outscores the previous team on total_score and KPI
        if self.n_team_stats['total_cost'] <= self.total_balance:
                self.team_list.append({
                    'team': self.n_team,
                    'stats': self.n_team_stats,
                    'replacements': self.replacements
                })



    def _copy_variables_for_wildcard(self):
        # make copies of variables to prevent them being over written on each iteration
        self.p_list = {}
        self.p_indicies = {}
        for pos in self.player_list:
            self.p_list[pos] = self.player_list[pos].copy()
            self.p_indicies[pos] = self.position_indicies[pos].copy()


    def generate_player_names_index_dict(self):
        # create a lookup dict for player name to find index/position
        # previously this was being done within the simulation slowing shit down
        player_index_lookup = {}
        for p in self.master_table:
            for pos in self.player_list:
                for idx, player in enumerate(self.player_list[pos]):
                    if player['web_name'] == p['web_name']:
                        player_index_lookup[player['web_name']] = {'index': idx, 'position': pos}
                        break
        return player_index_lookup

    @staticmethod
    def find_index_by_web_name(web_name, p_list):
        # pre allocate a dictionary for lookup before running the simulation
        for pos in p_list:
            for idx, player in enumerate(p_list[pos]):
                if web_name == player['web_name']:
                    return {'index': idx, 'position': pos}
        return False



    def find_n_replacements(self, num_replacements, desired, outfield_only, max_iterations=100000, order_by="total_score", num_teams=50):
        print('Starting an N Player Replacement simulation...')
        self.num_replacements = num_replacements
        self.desired = desired
        self.outfield_only = outfield_only
        self.max_iterations = max_iterations
        self.order_by = order_by
        self.num_teams = num_teams

        self.main_data_s = self._remove_currently_owned_players()
        self.player_list = self._split_main_data_by_position(self.main_data_s)
        self.player_index_lookup = self.generate_player_names_index_dict()

        self._get_position_indexes()

        if self.outfield_only:
            del self.player_list['G']

        self.start_replacement_simulation()

        if len(self.team_list) > 0:
            self.output_data()
        else:
            print('\nNo team improvements found for given input paramters. Sorry m8.')

    def start_replacement_simulation(self):
        self.team_list = []
        for i in range(self.max_iterations):
            self._copy_variables_for_replacement()
            self.replacements = []
            self._do_desired_replacements()
            self._do_random_replacements()
            self.n_team_stats = self.score_team(self.n_team)
            self._bad_team_filter()


    def _remove_currently_owned_players(self):
        # remove players in current team from master list to ensure that a new player is selected every time
        main_data = self.master_table.copy()
        team_name_list = [i['web_name'] for i in self.current_team]
        for idx, player in enumerate(main_data):
            if player['web_name'] in team_name_list:
                del main_data[idx]
        return main_data

    @staticmethod
    def _split_main_data_by_position(m_data):
        # create position specific player dict
        gk = filter_list_by_position(m_data, 'G')
        df = filter_list_by_position(m_data, 'D')
        md = filter_list_by_position(m_data, 'M')
        fw = filter_list_by_position(m_data, 'F')
        player_list = {'G': gk, 'D': df, 'M': md, 'F': fw}
        return player_list

    @staticmethod
    def score_team(t):
        sum_form_n = sum_value(t, 'form_n')
        sum_price_change_n = sum_value(t, 'price_change_n')
        sum_3_game_difficulty_n = sum_value(t, '3_game_difficulty_n')
        sum_ict_index_n = sum_value(t, 'ict_index_n')
        sum_KPI_n = sum_value(t, 'KPI_n')
        total_score = round(sum_form_n + sum_price_change_n - sum_3_game_difficulty_n + sum_ict_index_n, 2)
        total_cost = sum_value(t, 'price')
        return {
            'sum_form_n': sum_form_n,
            'sum_price_change_n': sum_price_change_n,
            'sum_3_game_difficulty_n': sum_3_game_difficulty_n,
            'sum_ict_index_n': sum_ict_index_n,
            'sum_KPI_n': sum_KPI_n,
            'total_cost': total_cost,
            'total_score': total_score
        }

    def _get_position_indexes(self):
        """
        Finds the indexes within the team in which each position occurs.
        Helps when finding a desired replacement within the Monte Carlo method.
        :return:
        """
        self.position_indicies = {
            'G': [],
            'D': [],
            'M': [],
            'F': []
        }
        for idx, player in enumerate(self.current_team):
            self.position_indicies[player['position']].append(idx)

        if self.outfield_only:
            del self.position_indicies['G']

    def _copy_variables_for_replacement(self):
        # make copies of variables to prevent them being over written on each iteration
        self.c_team = self.current_team.copy()
        self.n_team = self.current_team.copy()
        self.p_list = {}
        self.p_indicies = {}
        for pos in self.player_list:
            self.p_list[pos] = self.player_list[pos].copy()
            self.p_indicies[pos] = self.position_indicies[pos].copy()

    def _do_desired_replacements(self):
        # carry out desired replacements
        for player in self.desired:                                                 # find desired player index in p_list
            player_info = self.player_index_lookup[player]
            player_in = self.p_list[player_info['position']][player_info['index']]  # get desired player from p_list
            del self.p_list[player_info['position']][player_info['index']]          # delete desired player from p_list

            idx = random.randrange(len(self.p_indicies[player_info['position']]))   # select a random index from the desired player's postion
            index_old = self.p_indicies[player_info['position']][idx]               # convert this to a player index
            player_out = self.c_team[index_old]                                     # get the player out dict for this randomly selected player
            del self.p_indicies[player_info['position']][idx]                       # remove the selected index from the list so it can't be selected again
            if len(self.p_indicies[player_info['position']]) == 0:
                del self.p_indicies[player_info['position']]

            self.n_team[player_out['index']] = player_in                            # add new player to team list
            self.replacements.append({'old': player_out, 'new': player_in})         # update replacement object

    def _do_random_replacements(self):
        # carry out random replacements
        for j in range(self.num_replacements - len(self.desired)):
            pos_idx = random.choice(list(self.p_indicies.keys()))                       # choose a random position to replace
            idx = random.randrange(len(self.p_indicies[pos_idx]))                       # choose a random player from that position
            index_old = self.p_indicies[pos_idx][idx]
            player_out = self.c_team[index_old]                                         # get chosen player dict

            del self.p_indicies[pos_idx][idx]                                           # remove the selected index from the list so it can't be selected again
            if len(self.p_indicies[pos_idx]) == 0:                                       # if the position index is empty then remove it to prevent it being randomly selected
                del self.p_indicies[pos_idx]

            index_new = random.randrange(len(self.p_list[player_out['position']]))      # choose random player to replace
            player_in = self.p_list[player_out['position']][index_new]
            del self.p_list[player_out['position']][index_new]

            self.n_team[player_out['index']] = player_in                                # add new player to team list
            self.replacements.append({'old': player_out, 'new': player_in})             # update replacement object

    def _bad_team_filter(self):
        # only keep simulated team if it outscores the previous team on total_score and KPI
        if self.n_team_stats['total_cost'] <= self.total_balance:
            if self.n_team_stats['sum_KPI_n'] > self.current_team_stats['sum_KPI_n']:
                if self.n_team_stats['total_score'] > self.current_team_stats['total_score']:
                    self.team_list.append({
                        'team': self.n_team,
                        'stats': self.n_team_stats,
                        'replacements': self.replacements
                    })


    def _order_list(self):
        # sort team list by specified parameter
        if self.order_by == 'sum_3_game_difficulty_n':
            self.team_list_sorted = sorted(self.team_list, key=lambda k: k['stats'][self.order_by])
        else:
            self.team_list_sorted = sorted(self.team_list, key=lambda k: k['stats'][self.order_by], reverse=True)

    def _trim_list(self):
        # trim list to top number of specified results
        if len(self.team_list_sorted) > self.num_teams:
            self.team_list_sorted = self.team_list_sorted[:self.num_teams]

    @staticmethod
    def _create_substitutions_string(team):
        # concatenate replaced players into string
        replacement_string = ''
        for replacement in team['replacements']:
            replacement_string += replacement['old']['web_name'] + ' > ' + replacement['new']['web_name'] + '\n'
        return replacement_string

    @staticmethod
    def _create_team_string(team):
        # concatenate full team into string
        full_team = ''
        for player in team['team']:
            full_team += player['web_name'] + ", "
        return full_team

    def _generate_output_data(self):
        # construct the output list of data
        self.output = []
        for team in self.team_list_sorted:
            replacement_string = self._create_substitutions_string(team)
            team_string = self._create_team_string(team)

            # append team data to output variable
            self.output.append({
                'replacements': replacement_string,
                'full team': team_string,
                'new team form': team['stats']['sum_form_n'],
                'new team ICT': team['stats']['sum_ict_index_n'],
                'new team price change': team['stats']['sum_price_change_n'],
                'new team 3 game difficulty': team['stats']['sum_3_game_difficulty_n'],
                'new team score': team['stats']['total_score'],
                'new team KPI': team['stats']['sum_KPI_n'],
                'new team cost': team['stats']['total_cost'],
                'old team form': self.current_team_stats['sum_form_n'],
                'old team ICT': self.current_team_stats['sum_ict_index_n'],
                'old team price change': self.current_team_stats['sum_price_change_n'],
                'old team 3 game difficulty': self.current_team_stats['sum_3_game_difficulty_n'],
                'old team KPI': self.current_team_stats['sum_KPI_n'],
                'old team score': self.current_team_stats['total_score'],
                'old team cost': self.current_team_stats['total_cost'],
            })

    def _generate_output_data2(self):
        # construct the output list of data
        self.output = []
        for team in self.team_list_sorted:
            team_string = self._create_team_string(team)

            # append team data to output variable
            self.output.append({
                'full team': team_string,
                'new team form': team['stats']['sum_form_n'],
                'new team ICT': team['stats']['sum_ict_index_n'],
                'new team price change': team['stats']['sum_price_change_n'],
                'new team 3 game difficulty': team['stats']['sum_3_game_difficulty_n'],
                'new team score': team['stats']['total_score'],
                'new team KPI': team['stats']['sum_KPI_n'],
                'new team cost': team['stats']['total_cost'],
                'old team form': self.current_team_stats['sum_form_n'],
                'old team ICT': self.current_team_stats['sum_ict_index_n'],
                'old team price change': self.current_team_stats['sum_price_change_n'],
                'old team 3 game difficulty': self.current_team_stats['sum_3_game_difficulty_n'],
                'old team KPI': self.current_team_stats['sum_KPI_n'],
                'old team score': self.current_team_stats['total_score'],
                'old team cost': self.current_team_stats['total_cost'],
            })

    def output_data(self):

        self._order_list()
        self._trim_list()
        self._generate_output_data()
        generate_csv(self.output)

    def output_data2(self):

        self._order_list()
        self._trim_list()
        self._generate_output_data2()
        generate_csv(self.output)
