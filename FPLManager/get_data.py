import os.path
import pickle
import time

from FPLManager.process import ProcessData
from FPLManager.web_stuff import WebStuff


class GetData:
    def __init__(self, u, p, i, reduce, refresh):
        self.username = u
        self.password = p
        self.acc_id = i
        self.reduce = reduce
        self.refresh = refresh
        self.data = self.get_data()

    @staticmethod
    def save_to_pickle(variable, filename):
        with open(filename, 'wb') as handle:
            pickle.dump(variable, handle)

    @staticmethod
    def open_pickle(path_to_file):
        with open(path_to_file, 'rb') as handle:
            f = pickle.load(handle)
        return f

    @staticmethod
    def older_than_one_hour(file):
        current_time = time.time()
        last_modified_time = os.path.getmtime(file)
        if (current_time - last_modified_time) > (60 * 60):
            return True
        else:
            return False

    def use_cached_data(self):
        data = {
            'account_data': self.open_pickle('./data/account_data.pickle'),
            'master_table': self.open_pickle('./data/master_table.pickle'),
            'team_list': self.open_pickle('./data/team_list.pickle'),
            'team_info': self.open_pickle('./data/team_info.pickle'),
            'player_price_data': self.open_pickle('./data/player_price_data.pickle'),
            'player_stats_data': self.open_pickle('./data/player_stats_data.pickle')
        }

        return ProcessData(self.reduce, **data)

    def get_data_from_web(self):

        if not self.username or not self.password:
            print('\nProcess failed. Incomplete credentials supplied.')
            exit()

        web = WebStuff(self.username, self.password, self.acc_id)
        web.log_into_fpl()
        return ProcessData(self.reduce, web_session=web)

    def get_data(self):
        try:
            need_new_data = self.older_than_one_hour('./data/account_data.pickle')
        except:
            # no data exists
            return self.get_data_from_web()

        # data exists
        if need_new_data or self.refresh:
            return self.get_data_from_web()
        else:
            return self.use_cached_data()
