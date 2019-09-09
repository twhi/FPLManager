import json


class FplData:

    def __init__(self, session):
        print('Getting FPL data...')
        self.login_status = session.login_status
        self.session = session.session
        self.account_data = self.get_unique_account_data()
        self.team_info = self.get_team_list_data()
        self.account_data['bank'] = self.get_bank_value()
        self.master_table = self.get_master_table()
        self.team_ids = self.get_team_ids()
        self.account_data['next_event'] = self.next_event

    def get_bank_value(self):
        team_data_url = 'https://fantasy.premierleague.com/api/my-team/{0}/'.format(str(self.account_data['unique_id']))
        team_data_s = self.session.get(team_data_url).text
        return json.loads(team_data_s)['transfers']['bank']

    def get_unique_account_data(self):
        data = json.loads(self.session.get('https://fantasy.premierleague.com/api/me/').text)
        account_data = {
            'unique_id': data['player']['entry'],
            # 'bank': data['entry']['bank'] / 10,
        }
        return account_data

    def get_team_list_data(self):
        team_data_url = 'https://fantasy.premierleague.com/api/my-team/{0}/'.format(str(self.account_data['unique_id']))
        team_data_s = self.session.get(team_data_url).text
        return json.loads(team_data_s)['picks']

    def get_next_event(self, bs):
        for idx, e in enumerate(bs['events']):
            if e['is_next']:
                return bs['events'][idx]
        return None

    def get_team_ids(self):
        bs_static_s = self.session.get('https://fantasy.premierleague.com/api/bootstrap-static/').text
        bs_static = json.loads(bs_static_s)
        self.next_event = self.get_next_event(bs_static)
        teams_data = bs_static['teams']
        team_ids = {}
        for t in teams_data:
            team_ids[t['id']] = t['name']
        return team_ids

    def get_master_table(self):
        master_table_s = self.session.get('https://fantasy.premierleague.com/api/bootstrap-static/').text
        master_table = json.loads(master_table_s)
        return master_table['elements']
