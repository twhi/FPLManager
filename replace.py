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
    TODO: give this method some sort of dynamic naming functionality
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


class Replacement:
    def __init__(self, fpl_data, analysed_data):
        self.f_data = fpl_data
        self.total_balance = self.f_data.account_data['bank'] + self.f_data.account_data['total_balance']
        self.current_team = analysed_data.team_list
        self.master_table = analysed_data.master_table.copy()
        self.current_team_stats = self.score_team(self.current_team)
        self.outfield_only = None
        self.position_indicies = None


    def find_n_replacements(self, num_replacements, desired, outfield_only, max_iterations=100000, order_by="total_score", num_teams=50):
        main_data_s = self.remove_currently_owned_players()
        player_list = self.split_main_data_by_position(main_data_s)
        self.outfield_only = outfield_only
        self.get_position_indexes()

        if self.outfield_only:
            del player_list['G']

        team_list = self.start_monte_carlo(max_iterations, num_replacements, player_list, desired)

        if len(team_list) > 0:
            self.output_top_n(team_list, order_by, num_teams)
        else:
            print('\nNo team improvements found for given input paramters. Sorry m8.')

    def remove_currently_owned_players(self):
        # remove players in current team from master list to ensure that a new player is selected every time
        main_data = self.master_table.copy()
        team_name_list = [i['web_name'] for i in self.current_team]
        for idx, player in enumerate(main_data):
            if player['web_name'] in team_name_list:
                del main_data[idx]
        return main_data

    @staticmethod
    def split_main_data_by_position(m_data):
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

    @staticmethod
    def find_index_by_web_name(web_name, p_list):
        for pos in p_list:
            for idx, player in enumerate(p_list[pos]):
                if web_name == player['web_name']:
                    return {'index': idx, 'position': pos}
        return False

    def get_position_indexes(self):
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

    def start_monte_carlo(self, max_iterations, num_replacements, player_list, desired):
        new_team_list = []

        for i in range(max_iterations):
            # make a copy of current team to ensure that it isn't overwritten
            c_team = self.current_team.copy()
            n_team = self.current_team.copy()

            # make a copy of player_list
            p_list = {}
            p_indicies = {}
            for pos in player_list:
                p_list[pos] = player_list[pos].copy()
                p_indicies[pos] = self.position_indicies[pos].copy()

            # initialise replacements
            replacements = []

            # carry out desired replacements
            for player in desired:
                player_info = self.find_index_by_web_name(player, p_list)           # find desired player index in p_list
                player_in = p_list[player_info['position']][player_info['index']]   # get desired player from p_list
                del p_list[player_info['position']][player_info['index']]           # delete desired player from p_list

                idx = random.randrange(len(p_indicies[player_info['position']]))    # select a random index from the desired player's postion
                index_old = p_indicies[player_info['position']][idx]                # convert this to a player index
                player_out = c_team[index_old]                                      # get the player out dict for this randomly selected player
                del p_indicies[player_info['position']][idx]                        # remove the selected index from the list so it can't be selected again
                if len(p_indicies[player_info['position']]) == 0:
                    del p_indicies[player_info['position']]

                n_team[player_out['index']] = player_in                             # add new player to team list
                replacements.append({'old': player_out, 'new': player_in})          # update replacement object

            # carry out random replacements
            for j in range(num_replacements - len(desired)):
                # choose random player to take out of squad
                pos_idx = random.choice(list(p_indicies.keys()))                    # choose a random position to replace
                idx = random.randrange(len(p_indicies[pos_idx]))                    # choose a random player from that position
                index_old = p_indicies[pos_idx][idx]
                player_out = c_team[index_old]                                      # get chosen player dict
                del p_indicies[pos_idx][idx]                                        # remove the selected index from the list so it can't be selected again
                if len(p_indicies[pos_idx]) == 0:
                    del p_indicies[pos_idx]

                # choose random player to replace
                index_new = random.randrange(len(p_list[player_out['position']]))
                player_in = p_list[player_out['position']][index_new]
                del p_list[player_out['position']][index_new]

                # add new player to team list
                n_team[player_out['index']] = player_in

                # update replacement object
                replacements.append({'old': player_out, 'new': player_in})

            # score new team
            n_team_stats = self.score_team(n_team)

            # only keep simulated team if it outscores the previous team on ICT index, form, 3 game difficulty and price change probability
            if n_team_stats['total_cost'] <= self.total_balance:
                if n_team_stats['sum_ict_index_n'] > self.current_team_stats['sum_ict_index_n']:
                    if n_team_stats['sum_form_n'] > self.current_team_stats['sum_form_n']:
                        if n_team_stats['sum_3_game_difficulty_n'] < self.current_team_stats['sum_3_game_difficulty_n']:
                            if n_team_stats['sum_price_change_n'] > self.current_team_stats['sum_price_change_n']:
                                new_team_list.append(
                                    {'team': n_team, 'stats': n_team_stats, 'replacements': replacements})

            # # only keep simulated team if it outscores the previous team on ICT index, form, 3 game difficulty and price change probability
            # if n_team_stats['total_cost'] <= self.total_balance:
            #     if n_team_stats['sum_KPI_n'] > self.current_team_stats['sum_KPI_n']:
            #         new_team_list.append({
            #             'team': n_team,
            #             'stats': n_team_stats,
            #             'replacements': replacements
            #         })

        return new_team_list

    def output_top_n(self, team_list, order_by, num_teams):
        # 'order_by' parameters:
        # 'sum_form_n' - sum of the team's normalised form
        # 'sum_price_change_n' - sum of the team's normalised price change
        # 'sum_3_game_difficulty_n' - sum of the team's normalised game difficulty (higher = harder)
        # 'sum_ict_index_n' - sum of the team's ICT index (overall threat of the players)
        # 'total_score' - sum of the above

        # sort team list by specified parameter
        if order_by == 'sum_3_game_difficulty_n':
            team_list_sorted = sorted(team_list, key=lambda k: k['stats'][order_by])
        else:
            team_list_sorted = sorted(team_list, key=lambda k: k['stats'][order_by], reverse=True)

        # trim list to top number of specified results
        if len(team_list_sorted) > num_teams:
            team_list_sorted = team_list_sorted[:num_teams]

        output = []
        for idx, team in enumerate(team_list_sorted):
            # concatenate replaced players into string
            replacements = ''
            for replacement in team['replacements']:
                replacements += replacement['old']['web_name'] + ' > ' + replacement['new']['web_name'] + '\n'

            # concatenate full team into string
            full_team = ''
            for player in team['team']:
                full_team += player['web_name'] + ", "

            # append team data to output variable
            output.append({
                'replacements': replacements,
                'full team': full_team,
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

        # output data to csv
        generate_csv(output)
