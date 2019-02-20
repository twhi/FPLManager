from pulp import LpMinimize, LpMaximize, LpProblem, LpVariable, LpInteger
import itertools
import csv


def score_team(t, opt):
    sum_form_n = sum_value(t, 'form_n')
    sum_price_change_n = sum_value(t, 'price_change_n')
    sum_3_game_difficulty_n = sum_value(t, '3_game_difficulty_n')
    sum_ict_index_n = sum_value(t, 'ict_index_n')
    sum_KPI_n = sum_value(t, 'KPI_n')
    total_score = round(sum_form_n + sum_price_change_n - sum_3_game_difficulty_n + sum_ict_index_n, 2)
    sum_KPI_score = sum_value(t, 'KPI_score')
    total_opt_param = sum_value(t, opt)
    total_cost = sum_value(t, 'price')
    return {
        'sum_form_n': sum_form_n,
        'sum_price_change_n': sum_price_change_n,
        'sum_3_game_difficulty_n': sum_3_game_difficulty_n,
        'sum_ict_index_n': sum_ict_index_n,
        'sum_KPI_n': sum_KPI_n,
        'total_score': total_score,
        'sum_'+opt: total_opt_param,
        'sum_KPI_score': sum_KPI_score,
        'total_cost': total_cost
    }

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

class Substitution:
    def __init__(self, opt_parameter, data, optimal_team=False, n_subs=2):
        # set instance variables
        self.prob = None
        self.decision = None
        self.opt_max_min = None
        self.n_subs = n_subs
        self.opt_parameter = opt_parameter
        self.optimal_team = optimal_team
        self.max_price = 999
        self.output = []

        # split data parameters into data type
        self.master_table = data.master_table
        self.team_data = data.team_list
        self.account_data = data.account_data

        # remove existing players from master table
        # first make a copy of master table for output
        self.master_table_copy = self.master_table.copy()
        for idx, p in enumerate(self.master_table):
            for player in self.team_data:
                if player['id'] == p['id']:
                    self.master_table.pop(idx)

        # construct optimisation parameters lists
        self.player_list = [p['web_name'] for p in self.master_table]
        self.team_list = [p['team'] for p in self.master_table]
        self.master_team_list = [p['id'] for p in self.master_table]
        self.price_list = self.convert_str_list_to_float([p['price'] for p in self.master_table])
        self.opt_list = self.convert_str_list_to_float([p[self.opt_parameter] for p in self.master_table])

        # calculate more parameters
        self.define_opt_type()
        self.define_budget()

        # score current or 'old' team
        self.ots = score_team(self.team_data, self.opt_parameter)
        self.old_team_score = {}
        for key in self.ots:
            self.old_team_score['old_' + key] = self.ots[key]

        self.gk_list = self.create_position_list('G')
        self.df_list = self.create_position_list('D')
        self.md_list = self.create_position_list('M')
        self.fw_list = self.create_position_list('F')

        # sub combinations
        self.subs_to_make = self.get_subs()

        # get length of data
        self.data_length = range(len(self.player_list))

        # run some subs
        self.run_substitution_simulation()

        # output data
        keys = self.output[0].keys()
        with open('./output_data/substitution_sim.csv', 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(self.output)


    def run_substitution_simulation(self):
        idx = 0
        for subs in self.subs_to_make:
            idx += 1
            print(idx, 'out of', self.total_iterations, 'simulations complete', round(100*idx/self.total_iterations,2),'%')

            # create copy of current team
            self.current_team = self.team_data.copy()

            # remove selected players
            self.players_to_remove = []
            for sub in reversed(subs):
                self.players_to_remove.append(self.current_team[sub])
                self.current_team.pop(sub)

            # run optimiser
            self.subs = self.run_optimisation()

            #
            self.add_players_to_current_team()
            self.prepare_output()

    def get_player_data_by_webname(self, n):
        # should pre allocate this for speed
        for player in self.master_table:
            if player['web_name'] == n:
                return player

    def add_players_to_current_team(self):
        for player in self.subs:
            player_data = self.get_player_data_by_webname(player)
            self.current_team.append(player_data)

    def prepare_output(self):
        # get substitutions
        players_out = [p['web_name'] for p in self.players_to_remove]
        subs = [i + " > " + j for i, j in zip(players_out, self.subs)]
        new_team_score = score_team(self.current_team, self.opt_parameter)
        optimisation_data = {
            'subs': subs
        }
        optimisation_data.update(new_team_score)
        optimisation_data.update(self.old_team_score)

        self.output.append(optimisation_data)

        tester = True

    def get_subs(self):
        team_list = list(range(0,15))
        self.total_iterations = len(list(itertools.combinations(team_list, self.n_subs)))
        return itertools.combinations(team_list, self.n_subs)


    def define_budget(self):
        if not self.optimal_team:
            self.max_price = self.account_data['bank'] + self.account_data['total_balance']

    def define_opt_type(self):
        params_to_min = ['3_game_difficulty', '3_game_difficulty_n', 'price']
        if self.opt_parameter in params_to_min:
            self.opt_max_min = LpMinimize
        else:
            self.opt_max_min = LpMaximize

    def create_position_list(self, position):
        list_result = []
        for p in self.master_table:
            if p['position'] == position:
                list_result.append(1)
            else:
                list_result.append(0)
        return list_result

    def construct_list(self, attribute):
        l = []
        for player in self.master_table:
            l.append(player[attribute])
        return l

    @staticmethod
    def convert_str_list_to_float(lst):
        return [float(i) for i in lst]


    def print_opt_squad_data(self, squad):
        sum_opt = 0
        sum_price = 0
        for player in squad:
            player_data = self.lookup_player_by_web_name(player)
            print(player_data['web_name'])
            sum_opt += float(player_data[self.opt_parameter])
            sum_price += float(player_data['price'])
        print('\nTotal team cost £', round(sum_price,2))
        print('Total team', self.opt_parameter, round(sum_opt,2))

    def lookup_player_by_web_name(self, web_name):
        for p in self.master_table_copy:
            if p['web_name'] == web_name:
                return p

    def run_optimisation(self):

        # Declare problem instance, maximization problem
        self.prob = LpProblem("Squad", self.opt_max_min)

        # Declare decision variable x, which is 1 if a player is part of the squad and 0 else
        self.decision = LpVariable.matrix("decision", list(self.data_length), 0, 1, LpInteger)

        # Objective function -> Maximize specified optimisation parameter
        self.prob += sum(self.opt_list[i] * self.decision[i] for i in self.data_length)

        # add constraints
        self.add_sub_constraints()

        # solve problem
        self.prob.solve()

        # extract selected players and return
        return [self.player_list[i] for i in self.data_length if self.decision[i].varValue]

    def add_sub_constraints(self):

        # calculate these players attributes
        remove_positions = []
        player_out_cost = 0
        for player in self.players_to_remove:
            remove_positions.append(player['position'])     # [p['position'] for p in self.players_to_remove
            player_out_cost += float(player['price'])       # sum(item['gold'] for item in myLIst)
        new_budget = self.account_data['bank'] + player_out_cost

        # constrain the positions
        self.prob += sum(self.gk_list[i] * self.decision[i] for i in self.data_length) == remove_positions.count('G')
        self.prob += sum(self.df_list[i] * self.decision[i] for i in self.data_length) == remove_positions.count('D')
        self.prob += sum(self.md_list[i] * self.decision[i] for i in self.data_length) == remove_positions.count('M')
        self.prob += sum(self.fw_list[i] * self.decision[i] for i in self.data_length) == remove_positions.count('F')

        # total cost constraint
        self.prob += sum(self.price_list[i] * self.decision[i] for i in self.data_length) <= new_budget  # cost

        # num of players in team constraint
        team_id_list = [p['team'] for p in self.current_team]
        for i in range(1, 20):
            self.prob += sum([1 * self.decision[j] for j in range(len(team_id_list)) if team_id_list[j] == i]) + team_id_list.count(i) <= 3






class Wildcard:
    def __init__(self, opt_parameter, data, optimal_team=False):
        # set instance variables
        self.prob = None
        self.decision = None
        self.opt_max_min = None
        self.opt_parameter = opt_parameter
        self.optimal_team = optimal_team
        self.max_price = 999

        # split data parameters into data type
        self.master_table = data.master_table
        self.team_data = data.team_list
        self.account_data = data.account_data

        # construct optimisation parameters lists
        self.player_list = self.construct_list('web_name')
        self.team_list = self.construct_list('team')
        self.price_list = self.convert_str_list_to_float(self.construct_list('price'))
        self.opt_list = self.convert_str_list_to_float(self.construct_list(self.opt_parameter))

        # calculate more parameters
        self.define_opt_type()
        self.define_budget()
        self.gk_list = self.create_position_list('G')
        self.df_list = self.create_position_list('D')
        self.md_list = self.create_position_list('M')
        self.fw_list = self.create_position_list('F')

        self.data_length = range(len(self.player_list))
        self.squad = self.run_optimisation()

        # post processing
        self.print_opt_squad_data()


    def define_budget(self):
        if not self.optimal_team:
            self.max_price = self.account_data['bank'] + self.account_data['total_balance']

    def define_opt_type(self):
        params_to_min = ['3_game_difficulty', '3_game_difficulty_n', 'price']
        if self.opt_parameter in params_to_min:
            self.opt_max_min = LpMinimize
        else:
            self.opt_max_min = LpMaximize

    def create_position_list(self, position):
        list_result = []
        for p in self.master_table:
            if p['position'] == position:
                list_result.append(1)
            else:
                list_result.append(0)
        return list_result

    def construct_list(self, attribute):
        l = []
        for player in self.master_table:
            l.append(player[attribute])
        return l

    @staticmethod
    def convert_str_list_to_float(lst):
        return [float(i) for i in lst]

    def print_opt_squad_data(self):
        sum_opt = 0
        sum_price = 0
        for player in self.squad:
            player_data = self.lookup_player_by_web_name(player)
            print(player_data['web_name'], '-', player_data[self.opt_parameter])
            sum_opt += float(player_data[self.opt_parameter])
            sum_price += float(player_data['price'])
        print('\nTotal team cost - £', round(sum_price,2))
        print('Total team', self.opt_parameter,'-', round(sum_opt,2))

    def lookup_player_by_web_name(self, web_name):
        for p in self.master_table:
            if p['web_name'] == web_name:
                return p

    def run_optimisation(self):

        # Declare problem instance, maximization problem
        self.prob = LpProblem("Squad", self.opt_max_min)

        # Declare decision variable x, which is 1 if a player is part of the squad and 0 else
        self.decision = LpVariable.matrix("decision", list(self.data_length), 0, 1, LpInteger)

        # Objective function -> Maximize specified optimisation parameter
        self.prob += sum(self.opt_list[i] * self.decision[i] for i in self.data_length)

        # Constraint definition
        self.add_wildcard_constraints()

        # solve problem
        self.prob.solve()

        # extract selected players and return
        return [self.player_list[i] for i in self.data_length if self.decision[i].varValue]



    def add_wildcard_constraints(self):

        self.prob += sum(self.price_list[i] * self.decision[i] for i in self.data_length) <= self.max_price  # cost
        self.prob += sum(self.gk_list[i] * self.decision[i] for i in self.data_length) == 2  # number of goalies
        self.prob += sum(self.df_list[i] * self.decision[i] for i in self.data_length) == 5  # number of defenders
        self.prob += sum(self.md_list[i] * self.decision[i] for i in self.data_length) == 5  # number of midfielders
        self.prob += sum(self.fw_list[i] * self.decision[i] for i in self.data_length) == 3  # number of forwards

        for i in range(1,20):
            self.prob += sum([1 * self.decision[j] for j in self.data_length if self.team_list[j] == i]) <= 3


        ###################################
        # ALTERNATE METHOD (I THINK THIS WENT WRONG SOMEHOW)
        # Constraint definition
        # number_of_teams = 20
        # positions = ['G', 'D', 'M', 'F']
        # allowed_p = [2, 5, 5, 3]
        #
        # # constrain max price
        # self.prob += sum(self.price_list[i] * self.decision[i] for i in self.data_length) <= self.max_price  # cost
        #
        # # constrain number of players in each position
        # for idx, i in enumerate(positions):
        #     self.prob += sum([1 * self.decision[j] for j in self.data_length if self.position_list[j] == i]) <= \
        #                  allowed_p[idx]

        ender=True
