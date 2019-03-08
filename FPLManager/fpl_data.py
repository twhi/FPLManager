import json


class FplData:

    def __init__(self, session):
        print('Getting FPL data...')
        self.login_status = session.login_status
        self.session = session.session
        self.acc_id = session.acc_id
        self.account_data = self.get_unique_account_data()
        self.team_info = self.get_team_list_data()
        self.master_table = self.get_master_table()

    def get_unique_account_data(self):
        data = json.loads(self.session.get('https://fantasy.premierleague.com/drf/bootstrap-dynamic').text)
        account_data = {
            'unique_id': data['entry']['id'],
            'bank': data['entry']['bank'] / 10,
            'total_balance': data['entry']['value'] / 10
        }
        return account_data

    def get_team_list_data(self):
        team_data_url = 'https://fantasy.premierleague.com/drf/my-team/{0}/'.format(str(self.account_data['unique_id']))
        team_data_s = self.session.get(team_data_url).text
        return json.loads(team_data_s)['picks']


    def get_master_table(self):
        master_table_s = self.session.get('https://fantasy.premierleague.com/drf/elements').text
        master_table = json.loads(master_table_s)
        return master_table