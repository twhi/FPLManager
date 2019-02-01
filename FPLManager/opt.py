from pulp import LpMinimize, LpMaximize, LpProblem, LpVariable, LpInteger


class Optimise:
    def __init__(self, opt_parameter, data, optimal_team=False):
        self.prob = None
        self.decision = None

        self.opt_parameter = opt_parameter

        params_to_min = ['3_game_difficulty', '3_game_difficulty_n', 'price']

        if opt_parameter in params_to_min:
            self.opt_max_min = LpMinimize
        else:
            self.opt_max_min = LpMaximize

        if optimal_team:
            self.max_price = 999
        else:
            self.max_price = data.account_data['bank'] + data.account_data['total_balance']

        self.master_table = data.master_table
        self.account_data = data.account_data
        self.team_list = data.team_list

        self.gk_list = self.create_position_list('G')
        self.df_list = self.create_position_list('D')
        self.md_list = self.create_position_list('M')
        self.fw_list = self.create_position_list('F')

        self.player_list = self.construct_list('web_name')
        self.price_list = self.convert_str_list_to_float(self.construct_list('price'))
        self.team_list = self.construct_list('team')
        self.opt_list = self.convert_str_list_to_float(self.construct_list(self.opt_parameter))
        self.data_length = range(len(self.player_list))

        self.squad = self.run_optimisation()
        # self.get_full_squad_data()

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

    def get_full_squad_data(self):
        for player in self.squad:
            player_data = self.lookup_player_by_web_name(player)
            print(player_data['web_name'], player_data['team'], player_data[self.opt_parameter], sep=";")

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
        # Constraint definition
        number_of_teams = 20

        self.prob += sum(self.price_list[i] * self.decision[i] for i in self.data_length) <= self.max_price  # cost
        self.prob += sum(self.gk_list[i] * self.decision[i] for i in self.data_length) == 2  # number of goalies
        self.prob += sum(self.df_list[i] * self.decision[i] for i in self.data_length) == 5  # number of defenders
        self.prob += sum(self.md_list[i] * self.decision[i] for i in self.data_length) == 5  # number of midfielders
        self.prob += sum(self.fw_list[i] * self.decision[i] for i in self.data_length) == 3  # number of forwards

        for i in range(1,20):
            self.prob += sum([1 * self.decision[j] for j in self.data_length if self.team_list[j] == i]) <= 3

        ender=True
        # TODO: need to contrain the number of players from each team to 3, will need to do something similar to the positions
        # but in a for loop cos i aint gonna write out 20 lines