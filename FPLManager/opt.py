from pulp import LpMinimize, LpMaximize, LpProblem, LpVariable, LpInteger
import itertools
import csv
from time import gmtime, strftime


def score_team(t, opt):
    return {
        'team_form': sum(float(p['form']) for p in t),
        'team_price_change': sum(float(p['price_change']) for p in t),
        'team_3_game_difficulty': sum(float(p['3_game_difficulty']) for p in t),
        'team_ict_index': sum(float(p['ict_index']) for p in t),
        'team_KPI': sum(float(p['KPI']) for p in t),
        opt: sum(float(p[opt]) for p in t),
        'total_cost': sum(float(p['sell_price']) for p in t)
    }


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

        self.remove_owned_players()
        self.define_opt_type()
        self.define_budget()

        # construct optimisation parameters lists
        self.player_list = [p['web_name'] for p in self.master_table]
        self.id_list = [p['id'] for p in self.master_table]
        self.price_list = [float(item) / 10 for item in [p['now_cost'] for p in self.master_table]]
        self.opt_list = [float(item) for item in [p[self.opt_parameter] for p in self.master_table]]

        self.score_current_team()

        # create constraint containers
        self.pos_constraints = self.create_pos_constraints()
        self.team_constraints = self.create_team_constraints()

        # sub combinations
        self.subs_to_make = self.get_subs()

        # get length of data
        self.data_length = range(len(self.player_list))

        # run sub simulation
        self.run_substitution_simulation()

        self.output_data()

    def create_pos_constraints(self):
        positions = ['G', 'D', 'M', 'F']
        outlist = {}

        for pos in positions:
            list_result = []
            for p in self.master_table:
                if p['position'] == pos:
                    list_result.append(1)
                else:
                    list_result.append(0)
            outlist[pos] = list_result
        return outlist

    def create_team_constraints(self):
        teams = list(range(1, 21))
        outlist = {}

        for t in teams:
            list_result = []
            for p in self.master_table:
                if int(p['team']) == t:
                    list_result.append(1)
                else:
                    list_result.append(0)
            outlist[t] = list_result
        return outlist

    def create_constraint_switches_from_master(self, lookup, attr):
        '''
        Creates a dictionary of 'switches' which can be used to generate constraints in optimisation problems.
        This is fed with data from master_table.
        :param lookup: a list of values to lookup in master_table i.e. ['G', 'D', 'M', 'F']
        :param attr: the attribute in master_table to look for the lookup values i.e. 'position'
        :return: A dictionary of lists, where each list corresponds to a value in lookup
        '''
        outlist = {}
        for d in lookup:
            list_result = []
            for p in self.master_table:
                if p[attr] == d:
                    list_result.append(1)
                else:
                    list_result.append(0)
            outlist[d] = list_result
        return outlist

    def output_data(self):
        # output data
        output = sorted(self.output, key=lambda k: float(k[self.opt_parameter]), reverse=True)
        self.results = output
        keys = output[0].keys()
        fname = self.opt_parameter + '_' + str(self.n_subs) + '_' + strftime("%H%M%S", gmtime())
        with open('./output_data/' + fname + '.csv', 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(output)

    def score_current_team(self):
        # score current or 'old' team
        self.ots = score_team(self.team_data, self.opt_parameter)
        self.old_team_score = {}
        for key in self.ots:
            self.old_team_score['old_' + key] = self.ots[key]

    def remove_owned_players(self):
        # remove existing players from master table
        for player in self.team_data:
            for idx, p in enumerate(self.master_table):
                if player['id'] == p['id']:
                    self.master_table.pop(idx)

    def run_substitution_simulation(self):
        idx = 0
        self.best_score = 0
        for subs in self.subs_to_make:
            idx += 1
            print(idx, 'out of', self.total_iterations, 'simulations complete',
                  round(100 * idx / self.total_iterations, 2), '%')

            # create copy of current team
            self.current_team = self.team_data.copy()

            # remove selected players
            self.players_to_remove = []
            for sub in reversed(subs):
                self.players_to_remove.append(self.current_team[sub])
                self.current_team.pop(sub)

            # run optimiser
            self.subs, self.sub_names = self.run_optimisation()

            # post process
            self.add_players_to_current_team()
            self.prepare_output()
            # self.print_opt_squad_data()

    def get_player_data_by_id(self, n):
        # should pre allocate this for speed
        for player in self.master_table:
            if player['id'] == n:
                player.update({'sell_price': round(float(player['now_cost']), 1) / 10})
                return player

    def add_players_to_current_team(self):
        new_cost = 0
        for sub in self.subs:
            player_data = self.get_player_data_by_id(sub)
            new_cost += round(float(player_data['now_cost']), 1) / 10
            self.current_team.append(player_data)

    def prepare_output(self):
        # get substitutions
        players_out = [p['web_name'] for p in self.players_to_remove]
        subs = [i + " > " + j for i, j in zip(players_out, self.sub_names)]
        new_team_score = score_team(self.current_team, self.opt_parameter)
        optimisation_data = {
            'subs': subs
        }
        optimisation_data.update(new_team_score)
        optimisation_data.update(self.old_team_score)
        self.output.append(optimisation_data)

        if new_team_score[self.opt_parameter] > self.best_score:
            self.best_score = new_team_score[self.opt_parameter]
            self.best_team = self.current_team
            self.best_subs = subs

    def get_subs(self):
        team_list = list(range(0, 15))
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
        return [self.id_list[i] for i in self.data_length if self.decision[i].varValue], [self.player_list[i] for i in
                                                                                          self.data_length if
                                                                                          self.decision[i].varValue]

    def add_sub_constraints(self):

        # calculate new budget
        player_out_cost = sum(float(p['sell_price']) for p in self.players_to_remove)
        new_budget = self.account_data['bank'] + player_out_cost

        # calculate positions being removed
        remove_positions = [p['position'] for p in self.players_to_remove]

        # team constraints
        team_id_list = [p['team'] for p in self.current_team]
        for team in self.team_constraints:
            self.prob += sum(
                self.team_constraints[team][i] * self.decision[i] for i in self.data_length) + team_id_list.count(
                team) <= 3

        # position constraints
        for pos in self.pos_constraints:
            self.prob += sum(
                self.pos_constraints[pos][i] * self.decision[i] for i in self.data_length) == remove_positions.count(
                pos)

        # total cost constraint
        self.prob += sum(self.price_list[i] * self.decision[i] for i in self.data_length) <= new_budget


class Wildcard:
    def __init__(self, opt_parameter, data, optimal_team=False):
        # set instance variables
        self.prob = None
        self.decision = None
        self.opt_max_min = None
        self.opt_parameter = opt_parameter
        self.optimal_team = optimal_team
        self.max_price = 999
        self.max_players_per_position = {
            'G': 2,
            'D': 5,
            'M': 5,
            'F': 3
        }

        # split data parameters into data type
        self.master_table = data.master_table
        self.team_data = data.team_list
        self.account_data = data.account_data

        # construct optimisation parameters lists
        self.player_list = [p['web_name'] for p in self.master_table]
        self.id_list = [p['id'] for p in self.master_table]
        self.team_list = [p['team'] for p in self.master_table]
        self.master_team_list = [p['id'] for p in self.master_table]
        self.price_list = [float(item) / 10 for item in [p['now_cost'] for p in self.master_table]]
        self.opt_list = [float(item) for item in [p[self.opt_parameter] for p in self.master_table]]

        # calculate more parameters
        self.define_opt_type()
        self.define_budget()

        # create constraint containers
        self.pos_constraints = self.create_pos_constraints()
        self.team_constraints = self.create_team_constraints()

        self.data_length = range(len(self.player_list))
        self.squad_ids = self.run_optimisation()
        self.squad = self.lookup_team_by_id()

    def lookup_team_by_id(self):
        team_list = []
        for id in self.squad_ids:
            for p in self.master_table:
                if p['id'] == id:
                    team_list.append(p)
        return team_list

    def create_pos_constraints(self):
        positions = ['G', 'D', 'M', 'F']
        outlist = {}

        for pos in positions:
            list_result = []
            for p in self.master_table:
                if p['position'] == pos:
                    list_result.append(1)
                else:
                    list_result.append(0)
            outlist[pos] = list_result
        return outlist

    def create_team_constraints(self):
        teams = list(range(1, 21))
        outlist = {}

        for t in teams:
            list_result = []
            for p in self.master_table:
                if int(p['team']) == t:
                    list_result.append(1)
                else:
                    list_result.append(0)
            outlist[t] = list_result
        return outlist

    def create_constraint_switches_from_master(self, lookup, attr):
        '''
        Creates a dictionary of 'switches' which can be used to generate constraints in optimisation problems.
        This is fed with data from master_table.
        :param lookup: a list of values to lookup in master_table i.e. ['G', 'D', 'M', 'F']
        :param attr: the attribute in master_table to look for the lookup values i.e. 'position'
        :return: A dictionary of lists, where each list corresponds to a value in lookup
        '''
        outlist = {}
        for d in lookup:
            list_result = []
            for p in self.master_table:
                if p[attr] == d:
                    list_result.append(1)
                else:
                    list_result.append(0)
            outlist[d] = list_result
        return outlist

    def create_team_list(self, team):
        list_result = []
        for p in self.master_table:
            if int(p['team']) == team:
                list_result.append(1)
            else:
                list_result.append(0)
        return list_result

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
        return [self.id_list[i] for i in self.data_length if self.decision[i].varValue]

    def add_wildcard_constraints(self):

        # team constraints
        for team in self.team_constraints:
            self.prob += sum(self.team_constraints[team][i] * self.decision[i] for i in self.data_length) <= 3

        # position constraints
        for pos in self.pos_constraints:
            self.prob += sum(self.pos_constraints[pos][i] * self.decision[i] for i in self.data_length) == \
                         self.max_players_per_position[pos]

        # price constraint
        self.prob += sum(self.price_list[i] * self.decision[i] for i in self.data_length) <= self.max_price  # cost
