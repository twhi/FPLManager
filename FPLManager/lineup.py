class Lineup:
    def __init__(self, team, param):
        self.formations = {
            '532': [1, 5, 3, 2],
            '523': [1, 5, 2, 3],
            '541': [1, 5, 4, 1],
            '451': [1, 4, 5, 1],
            '442': [1, 4, 4, 2],
            '433': [1, 4, 3, 3],
            '352': [1, 3, 5, 2],
            '343': [1, 3, 4, 3],
        }

        self.positions = ['G', 'D', 'M', 'F']

        self.team_by_position = {
            'G': [],
            'D': [],
            'M': [],
            'F': []
        }

        self.param = param
        self.team_unsorted = team
        self.sort_team_by_param()
        self.sort_team_by_position()
        self.lineup = self.choose_optimal_lineup()

    def sort_team_by_param(self):
        self.team = sorted(self.team_unsorted, key=lambda k: float(k[self.param]), reverse=True)

    def sort_team_by_position(self):
        for player in self.team:
            self.team_by_position[player['position']].append(player)

    def choose_optimal_lineup(self):
        best_score = 0
        for formation in self.formations:
            # add players to squad
            lineup = []
            subs = []
            for pos, num in zip(self.positions, self.formations[formation]):
                lineup += self.team_by_position[pos][:num]
                subs += self.team_by_position[pos][num:]

            # calculate the score
            score = sum(float(p[self.param]) for p in lineup)

            # find max value i.e. captain choice
            cap = max(lineup, key=lambda x: float(x[self.param]))

            # if it's the best one yet then save it
            if score > best_score:
                best_score = score
                best = {
                    'formation': self.formations[formation],
                    'score': score,
                    'lineup': lineup,
                    'captain': cap['web_name'],
                    'subs': subs
                }
        return best

    def print_lineup(self):
        print('##################')
        print('Optimal lineup -', self.lineup['formation'], '\n')

        print('Starting 11:')
        for p in self.lineup['lineup']:
            if p['web_name'] == self.lineup['captain']:
                print('(c)', '-', p['web_name'], p[self.param])
            else:
                print(p['web_name'], p[self.param], sep=' - ')
        print('\n')

        print('Subs:')
        for p in self.lineup['subs']:
            print(p['web_name'], p[self.param], sep=' - ')
        print('\n')
        print('Starting 11\'s', self.param, '-', round(self.lineup['score'], 1))
