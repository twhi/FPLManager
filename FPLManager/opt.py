from pulp import LpMaximize, LpProblem, LpVariable, LpInteger, lpSum


def score_team(t, opt):
    return {
        'team_form': sum(float(p['form']) for p in t),
        'team_price_change': sum(float(p['price_change']) for p in t),
        'num_games': sum(float(p['next_gameweek']) for p in t),
        'team_KPI': sum(float(p['KPI']) for p in t),
        opt: sum(float(p[opt]) for p in t),
        'total_cost': sum(float(p['sell_price']) for p in t)
    }


class Opt:
    max_players_per_position = {
        'G': 2,
        'D': 5,
        'M': 5,
        'F': 3
    }

    def __init__(self, opt_parameter, data, n_subs=None, budget=999, desired=None, remove=None):
        # set instance variables
        self.max_price = budget
        self.prob = None
        self.decision = None
        self.opt_max_min = None

        if n_subs:
            self.wildcard = False
            self.n_subs = n_subs
        else:
            self.wildcard = True

        self.desired = desired
        self.remove = remove
        self.opt_parameter = opt_parameter
        self.output = []

        # split data parameters into data type
        self.master_table = data.master_table
        self.team_data = data.team_list
        self.account_data = data.account_data

        # use the number of games in the next gameweek to weight the optimisation parameter
        # need to be VERY careful if this is a good idea or not
        self.opt_list = []
        for p in self.master_table:
            if p[self.opt_parameter]:
                self.opt_list.append(float(p[self.opt_parameter]) * p['next_gameweek'])
            else:
                self.opt_list.append(0)

        # score current team
        self.score_current_team()

        # construct optimisation parameters lists
        # if players to exclude have been specified then mark these
        if self.remove:
            self.mark_players_to_exclude()
            self.remove_constraints = [p['remove'] for p in self.master_table]

        # if players to include have been specified then mark these
        if self.desired:
            self.mark_players_to_include()
            self.desired_constraints = [p['desired'] for p in self.master_table]

        # if it is not a wildcard sim (i.e. a transfer sim) then mark currently owned players
        if not self.wildcard:
            self.mark_owned_players()
            self.in_team_constraints = [p['in_team'] for p in self.master_table]

        self.id_list = [p['id'] for p in self.master_table]
        self.price_list = [float(item) for item in [p['sell_price'] for p in self.master_table]]

        pos_lookup = ['G', 'D', 'M', 'F']
        self.pos_constraints = self.create_constraint_switches_from_master(pos_lookup, 'position')
        team_lookup = list(range(1, 21))
        self.team_constraints = self.create_constraint_switches_from_master(team_lookup, 'team')

        # get length of data
        self.data_length = range(len(self.id_list))

        # run simulation and post processing
        self.squad_ids = self.run_optimisation()
        self.squad = self.lookup_team_by_id()

    @classmethod
    def wildcard_simulation(cls, opt_param, data, budget, desired=None, remove=None):
        n_subs = 0
        return cls(opt_param, data, n_subs, budget, desired, remove)

    @classmethod
    def transfer_simulation(cls, opt_param, data, n_subs, budget, desired=None, remove=None):
        return cls(opt_param, data, n_subs, budget, desired, remove)

    def mark_players_to_exclude(self):
        for p in self.master_table:
            p['remove'] = 0

        for rem in self.remove:
            for p in self.master_table:
                if rem == p['web_name']:
                    p['remove'] = 1

    def mark_players_to_include(self):
        for p in self.master_table:
            p['desired'] = 0

        for des in self.desired:
            for p in self.master_table:
                if des == p['web_name']:
                    p['desired'] = 1

    def mark_owned_players(self):
        # remove existing players from master table
        for p in self.master_table:
            p['in_team'] = 0

        for player in self.team_data:
            for idx, p in enumerate(self.master_table):
                if player['id'] == p['id']:
                    p['in_team'] = 1

    def calculate_improvement(self):
        old_squad_score = sum(float(p[self.opt_parameter]) for p in self.team_data)
        new_squad_score = sum(float(p[self.opt_parameter]) for p in self.squad)
        return old_squad_score, new_squad_score

    def extract_subs(self):
        # get players that are being subbed out
        existing_player_u = [i for i in self.team_data if i not in self.squad]
        existing_player = sorted(existing_player_u, key=lambda k: k['position'], reverse=True)

        # get players that are being subbed in
        sub_u = [i for i in self.squad if i not in self.team_data]
        sub = sorted(sub_u, key=lambda k: k['position'], reverse=True)

        return existing_player, sub

    def lookup_team_by_id(self):
        team_list = []
        for i in self.squad_ids:
            for p in self.master_table:
                if p['id'] == i:
                    team_list.append(p)
        return team_list

    def create_constraint_switches_from_master(self, lookup, attr):
        """
        Creates a dictionary of 'switches' which can be used to generate constraints in optimisation problems.
        This is fed with data from master_table.
        :param lookup: a list of values to lookup in master_table i.e. ['G', 'D', 'M', 'F']
        :param attr: the attribute in master_table to look for the lookup values i.e. 'position'
        :return: A dictionary of lists, where each list corresponds to a value in lookup
        """
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

    def score_current_team(self):
        # score current or 'old' team
        self.ots = score_team(self.team_data, self.opt_parameter)
        self.old_team_score = {}
        for key in self.ots:
            self.old_team_score['old_' + key] = self.ots[key]

    def run_optimisation(self):

        # Declare problem instance, max/min problem
        self.prob = LpProblem("Squad", LpMaximize)

        # Declare decision variable - 1 if a player is part of the squad else 0
        self.decision = LpVariable.matrix("decision", list(self.data_length), 0, 1, LpInteger)

        # Objective function -> Maximize specified optimisation parameter
        self.prob += lpSum(self.opt_list[i] * self.decision[i] for i in self.data_length)

        # Constraint definition
        self.add_constraints()

        # solve problem
        self.prob.solve()

        # extract selected players and return
        return [self.id_list[i] for i in self.data_length if self.decision[i].varValue]

    def add_constraints(self):

        # team constraints
        # maximum of 3 players per team
        for team in self.team_constraints:
            self.prob += lpSum(self.team_constraints[team][i] * self.decision[i] for i in self.data_length) <= 3

        # position constraints
        # constrains the team to have 2 GK, 5 DEF, 5 MIN and 3 FW
        for pos in self.pos_constraints:
            self.prob += lpSum(self.pos_constraints[pos][i] * self.decision[i] for i in self.data_length) == \
                         self.max_players_per_position[pos]

        # price constraint
        # limits the overall price of the team
        self.prob += lpSum(self.price_list[i] * self.decision[i] for i in self.data_length) <= self.max_price

        # desired player constraint
        if self.desired:
            self.prob += lpSum(self.desired_constraints[i] * self.decision[i] for i in self.data_length) == len(
                self.desired)

        # players to remove constraint
        if self.remove:
            self.prob += lpSum(self.remove_constraints[i] * self.decision[i] for i in self.data_length) == 0

        # initial squad constraint - ONLY USE IN TRANSFER SIMULATION
        # ensures that the final team has (15 - number of subs) players from the initial team
        if not self.wildcard:
            self.prob += lpSum(
                self.in_team_constraints[i] * self.decision[i] for i in self.data_length) == 15 - self.n_subs
