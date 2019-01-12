import csv
import random

from main import analysis, sum_value


class Replacement:
    def __init__(self, fpl_data, analysed_data):
        self.f_data = fpl_data
        self.analysis = analysed_data
        self.total_balance = self.f_data.account_data['bank'] + self.f_data.account_data['total_balance']
        self.current_team = analysis.team_list
        self.master_table = analysis.master_table.copy()
        self.c_team_stats = self.score_team(self.current_team)

    def find_n_replacements(self, num_replacements, max_iterations=100000, order_by="total_score", num_teams=50):
        main_data_s = self.remove_currently_owned_players()
        player_list = self.split_main_data_by_position(main_data_s)
        team_list = self.start_monte_carlo(max_iterations, num_replacements, player_list)
        self.output_top_n(team_list, order_by, num_teams)

    def remove_currently_owned_players(self):
        # remove players in current team from master list to ensure that a new player is selected every time
        main_data = self.master_table.copy()
        team_name_list = [i['web_name'] for i in self.current_team]
        for idx, player in enumerate(main_data):
            if player['web_name'] in team_name_list:
                del main_data[idx]
        return main_data

    def split_main_data_by_position(self, m_data):
        # create position specific player dict
        gk = self.filter_list_by_position(m_data, 'G')
        df = self.filter_list_by_position(m_data, 'D')
        md = self.filter_list_by_position(m_data, 'M')
        fw = self.filter_list_by_position(m_data, 'F')
        player_list = {'G': gk, 'D': df, 'M': md, 'F': fw}
        return player_list

    @staticmethod
    def score_team(t):
        sum_form_n = sum_value(t, 'form_n')
        sum_price_change_n = sum_value(t, 'price_change_n')
        sum_3_game_difficulty_n = sum_value(t, '3_game_difficulty_n')
        sum_ict_index_n = sum_value(t, 'ict_index_n')
        total_score = round(sum_form_n + sum_price_change_n - sum_3_game_difficulty_n + sum_ict_index_n, 2)
        total_cost = sum_value(t, 'price')
        return {
            'sum_form_n': sum_form_n,
            'sum_price_change_n': sum_price_change_n,
            'sum_3_game_difficulty_n': sum_3_game_difficulty_n,
            'sum_ict_index_n': sum_ict_index_n,
            'total_cost': total_cost,
            'total_score': total_score
        }

    def start_monte_carlo(self, max_iterations, num_replacements, player_list):
        new_team_list = []
        for i in range(max_iterations):
            # make a copy of current team to ensure that it isn't overwritten
            c_team = self.current_team.copy()
            n_team = self.current_team.copy()

            # make a copy of player_list
            p_list = {}
            for pos in player_list:
                p_list[pos] = player_list[pos].copy()

            # carry out replacements
            replacements = []
            for j in range(num_replacements):
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
            n_team_stats = self.score_team(n_team)

            if n_team_stats['total_cost'] <= self.total_balance:
                if n_team_stats['sum_ict_index_n'] > self.c_team_stats['sum_ict_index_n']:
                    if n_team_stats['sum_form_n'] > self.c_team_stats['sum_form_n']:
                        if n_team_stats['sum_3_game_difficulty_n'] < self.c_team_stats['sum_3_game_difficulty_n']:
                            if n_team_stats['sum_price_change_n'] > self.c_team_stats['sum_price_change_n']:
                                new_team_list.append(
                                    {'team': n_team, 'stats': n_team_stats, 'replacements': replacements})
        return new_team_list

    def output_top_n(self, team_list, order_by, num_teams):
        '''
        'order_by' parameters:
        'sum_form_n' - sum of the team's normalised form
        'sum_price_change_n' - sum of the team's normalised price change
        'sum_3_game_difficulty_n' - sum of the team's normalised game difficulty (higher = harder)
        'sum_ict_index_n' - sum of the team's ICT index (overall threat of the players)
        'total_score' - sum of the above
        '''

        # sort team list
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
                'new team cost': team['stats']['total_cost'],
                'old team form': self.c_team_stats['sum_form_n'],
                'old team ICT': self.c_team_stats['sum_ict_index_n'],
                'old team price change': self.c_team_stats['sum_price_change_n'],
                'old team 3 game difficulty': self.c_team_stats['sum_3_game_difficulty_n'],
                'old team score': self.c_team_stats['total_score'],
                'old team cost': self.c_team_stats['total_cost'],
            })

        # output data to csv
        self.generate_csv(output)

    @staticmethod
    def filter_list_by_position(data, position):
        outlist = []
        for player in data:
            if player['position'] == position:
                outlist.append(player)
        return outlist

    @staticmethod
    def generate_csv(output):
        keys = output[0].keys()
        with open('output.csv', 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(output)