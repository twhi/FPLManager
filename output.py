import csv


class Output:
    def __init__(self, output):
        # output = list of dicts
        self.output = output
        # self.headers = ['web_name', 'position', 'form', 'price', 'price_change', '3_game_difficulty', 'form_per_price']
        self.headers = False
    def trim_and_output_data(self):
        team_list = []
        for player in self.output:
            if self.headers:
                player_dict = dict((k, player[k]) for k in self.headers if k in player)
                team_list.append(player_dict)

        # output file to csv
        keys = team_list[0].keys()
        with open('output.csv', 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(team_list)
