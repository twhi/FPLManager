import json


class FplData:

    def __init__(self, session):
        self.session = session
        self.account_data = self.get_unique_account_data()
        self.team_data = self.get_team_data()
        self.master_data = self.get_master_data()

    def get_unique_account_data(self):
        data = json.loads(self.session.get('https://fantasy.premierleague.com/drf/bootstrap-dynamic').text)
        account_data = {
            'unique_id': data['entry']['id'],
            'bank': data['entry']['bank'] / 10,
            'total_balance': data['entry']['value'] / 10
        }
        return account_data

    def get_team_data(self):
        team_data_url_template = 'https://fantasy.premierleague.com/drf/my-team/[account_id]/'
        team_data_url = team_data_url_template.replace('[account_id]', str(self.account_data['unique_id']))
        team_data_s = self.session.get(team_data_url).text
        return json.loads(team_data_s)['picks']

    def get_master_data(self):
        master_table_s = self.session.get('https://fantasy.premierleague.com/drf/elements').text
        master_table = json.loads(master_table_s)
        return master_table