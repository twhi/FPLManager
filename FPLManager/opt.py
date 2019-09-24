from pulp import LpMinimize, LpMaximize, LpProblem, LpVariable, LpInteger
import itertools
import csv
from time import gmtime, strftime


def score_team(t, opt):
    return {
        'team_form': sum(float(p['form']) for p in t),
        'team_price_change': sum(float(p['price_change']) for p in t),
        'num_games': sum(float(p['next_gameweek']) for p in t),
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

        self.define_opt_type()
        self.define_budget()

        # construct optimisation parameters lists
        self.player_list = [p['web_name'] for p in self.master_table]
        self.id_list = [p['id'] for p in self.master_table]
        self.price_list = [float(item) / 10 for item in [p['now_cost'] for p in self.master_table]]

        # use the number of games in the next gameweek to weight the optimisation parameter
        # need to be VERY careful if this is a good idea or not
        self.opt_list = [float(p[self.opt_parameter]) * p['next_gameweek'] for p in self.master_table]
        # self.opt_list = [float(p[self.opt_parameter])for p in self.master_table]

        self.score_current_team()

        # create constraint containers
        self.mark_owned_players()
        self.in_team_constraints = [p['in_team'] for p in self.master_table]

        pos_lookup = ['G', 'D', 'M', 'F']
        self.pos_constraints = self.create_constraint_switches_from_master(pos_lookup, 'position')
        team_lookup = list(range(1, 21))
        self.team_constraints = self.create_constraint_switches_from_master(team_lookup, 'team')

        # get length of data
        self.data_length = range(len(self.player_list))

        self.squad_ids = self.run_optimisation()
        self.squad = self.lookup_team_by_id()

    def extract_subs(self):
        existing_player_u = [i for i in self.team_data if i not in self.squad]
        existing_player = sorted(existing_player_u, key=lambda k: k['position'], reverse=True)

        sub_u = [i for i in self.squad if i not in self.team_data]
        sub = sorted(sub_u, key=lambda k: k['position'], reverse=True)

        return existing_player, sub

    def lookup_team_by_id(self):
        team_list = []
        for id in self.squad_ids:
            for p in self.master_table:
                if p['id'] == id:
                    team_list.append(p)
        return team_list

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

    def mark_owned_players(self):
        # remove existing players from master table
        for p in self.master_table:
            p['in_team'] = 0

        for player in self.team_data:
            for idx, p in enumerate(self.master_table):
                if player['id'] == p['id']:
                    p['in_team'] = 1

    def get_player_data_by_id(self, n):
        # should pre allocate this for speed
        for player in self.master_table:
            if player['id'] == n:
                player.update({'sell_price': round(float(player['now_cost']), 1) / 10})
                return player

    def define_budget(self):
        if not self.optimal_team:
            self.max_price = self.account_data['bank'] / 10 + self.account_data['total_balance']

    def define_opt_type(self):
        params_to_min = ['3_game_difficulty', '3_game_difficulty_n', 'price']
        if self.opt_parameter in params_to_min:
            self.opt_max_min = LpMinimize
        else:
            self.opt_max_min = LpMaximize

    def run_optimisation(self):

        # Declare problem instance, max/min problem
        self.prob = LpProblem("Squad", self.opt_max_min)

        # Declare decision variable x, which is 1 if a player is part of the squad else 0
        self.decision = LpVariable.matrix("decision", list(self.data_length), 0, 1, LpInteger)

        # Objective function -> Maximize specified optimisation parameter
        self.prob += sum(self.opt_list[i] * self.decision[i] for i in self.data_length)

        # Constraint definition
        self.add_sub_constraints()

        # solve problem
        self.prob.solve()

        # extract selected players and return
        return [self.id_list[i] for i in self.data_length if self.decision[i].varValue]

    def add_sub_constraints(self):

        # team constraints
        # maximum of 3 players per team
        for team in self.team_constraints:
            self.prob += sum(self.team_constraints[team][i] * self.decision[i] for i in self.data_length) <= 3

        # position constraints
        # constrains the team to have 2 GK, 5 DEF, 5 MIN and 3 FW
        for pos in self.pos_constraints:
            self.prob += sum(self.pos_constraints[pos][i] * self.decision[i] for i in self.data_length) == \
                         self.max_players_per_position[pos]

        # price constraint
        # limits the overall price of the team
        self.prob += sum(self.price_list[i] * self.decision[i] for i in self.data_length) <= self.max_price  # cost

        # initial squad constraint
        # ensures that the final team has (15 - number of subs) players from the initial team
        self.prob += sum(self.in_team_constraints[i] * self.decision[i] for i in self.data_length) == 15 - self.n_subs


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
        # self.team_list = [p['team'] for p in self.master_table]
        # self.master_team_list = [p['id'] for p in self.master_table]
        self.price_list = [float(p['now_cost']) / 10 for p in self.master_table]

        # use the number of games in the next gameweek to weight the optimisation parameter
        # need to be VERY careful if this is a good idea or not
        self.opt_list = [float(p[self.opt_parameter]) * p['next_gameweek'] for p in self.master_table]
        # self.opt_list = [float(p[self.opt_parameter]) for p in self.master_table]

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
            self.max_price = (self.account_data['bank'] / 10) + self.account_data['total_balance']

    def define_opt_type(self):
        params_to_min = ['3_game_difficulty', '3_game_difficulty_n', 'price']
        if self.opt_parameter in params_to_min:
            self.opt_max_min = LpMinimize
        else:
            self.opt_max_min = LpMaximize

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
