from pulp import LpMinimize, LpMaximize, LpProblem, LpVariable, LpInteger



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

        self.gk_list = self.create_position_list('G')
        self.df_list = self.create_position_list('D')
        self.md_list = self.create_position_list('M')
        self.fw_list = self.create_position_list('F')

        self.data_length = range(len(self.player_list))
        self.subs = self.run_optimisation()

        prev_team_opt_val = 0
        for p in self.team_data:
            prev_team_opt_val += float(p[self.opt_parameter])


        # grab data for sub'd players
        sub_data = []
        for sub in self.subs:
            sub_data.append(self.lookup_player_by_web_name(sub))

        print('################')
        print('Substitutions made\n')
        old_opt_value = 0
        new_opt_value = 0
        for idx, removed in enumerate(self.players_to_remove):
            old_opt_value += float(removed[self.opt_parameter])
            new_opt_value += float(sub_data[idx][self.opt_parameter])
            print(removed['web_name'], '>', sub_data[idx]['web_name'])

        delta = round(new_opt_value - old_opt_value, 2)

        # post processing
        final_squad = self.team_name_list + self.subs

        print('\n################')
        print('Final squad\n')
        self.print_opt_squad_data(final_squad)
        print('This substitution increased', self.opt_parameter, 'by ', delta)
        print('(Old team', self.opt_parameter, 'was', round(prev_team_opt_val, 2), ')')

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

        # find number of players that minimise the opt param
        team_opt_list = sorted(self.team_data, key=lambda k: float(k[self.opt_parameter]))
        self.players_to_remove = []
        for idx, i in enumerate(range(self.n_subs)):
            self.players_to_remove.append(team_opt_list[i]) # index out of range error
            team_opt_list.pop(idx)


        # calculate these players attributes
        remove_positions = []
        player_out_cost = 0
        for player in self.players_to_remove:
            remove_positions.append(player['position'])
            player_out_cost += float(player['price'])
        new_budget = self.account_data['bank'] + player_out_cost

        # get current team ID list
        team_id_list = [p['team'] for p in team_opt_list]

        # get current team name list
        self.team_name_list = [p['web_name'] for p in team_opt_list]


        if remove_positions.count('G'):
            self.prob += sum(self.gk_list[i] * self.decision[i] for i in self.data_length) == remove_positions.count('G')

        if remove_positions.count('D'):
            self.prob += sum(self.df_list[i] * self.decision[i] for i in self.data_length) == remove_positions.count('D')

        if remove_positions.count('M'):
            self.prob += sum(self.md_list[i] * self.decision[i] for i in self.data_length) == remove_positions.count('M')

        if remove_positions.count('F'):
            self.prob += sum(self.fw_list[i] * self.decision[i] for i in self.data_length) == remove_positions.count('F')

        # total cost constraint
        self.prob += sum(self.price_list[i] * self.decision[i] for i in self.data_length) <= new_budget  # cost

        # num of players in team constraint
        # for i in range(1,20):
        #     self.prob += sum([1 * self.decision[j] for j in range(len(team_id_list)) if team_id_list[j] == i]) + team_id_list.count(i) <= 3

        for i in range(1,20):
            self.prob += sum([1 * self.decision[j] for j in self.data_length if self.team_list[j] == i]) <= 3



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






class Optimise:
    def __init__(self, opt_parameter, data, optimal_team=False, sim_type='sub', n_subs=2):
        # set instance variables
        self.prob = None
        self.decision = None
        self.opt_max_min = None
        self.sim_type = sim_type
        self.n_subs = n_subs
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
            print(player_data['web_name'])
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
        if self.sim_type == 'wildcard':
            self.add_wildcard_constraints()
        elif self.sim_type == 'sub':
            self.add_sub_constraints()

        # solve problem
        self.prob.solve()

        # extract selected players and return
        return [self.player_list[i] for i in self.data_length if self.decision[i].varValue]

    def add_sub_constraints(self):

        # find number of players that minimise the opt param
        team_opt_list = sorted(self.team_data, key=lambda k: float(k[self.opt_parameter]))
        players_to_remove = []
        for i in range(self.n_subs):
            players_to_remove.append(team_opt_list[i])

        # find these players
        remove_positions = []
        player_out_cost = 0
        for player in players_to_remove:
            remove_positions.append(player['position'])
            player_out_cost += float(player['price'])
        new_budget = self.account_data['bank'] + player_out_cost

        # get current team ID list
        team_id_list = [p['id'] for p in self.team_data]


        if remove_positions.count('G'):
            self.prob += sum(self.gk_list[i] * self.decision[i] for i in self.data_length) == remove_positions.count('G')

        if remove_positions.count('D'):
            self.prob += sum(self.df_list[i] * self.decision[i] for i in self.data_length) == remove_positions.count('D')

        if remove_positions.count('M'):
            self.prob += sum(self.md_list[i] * self.decision[i] for i in self.data_length) == remove_positions.count('M')

        if remove_positions.count('F'):
            self.prob += sum(self.fw_list[i] * self.decision[i] for i in self.data_length) == remove_positions.count('F')

        # total cost constraint
        self.prob += sum(self.price_list[i] * self.decision[i] for i in self.data_length) <= new_budget  # cost

        # num of players from a team constraint
        for i in range(1,20):
            self.prob += sum([1 * self.decision[j] for j in self.data_length if self.team_list[j] == i]) <= 3



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
