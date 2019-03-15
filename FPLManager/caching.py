import pickle

def save_to_pickle(variable, filename):
    with open(filename, 'wb') as handle:
        pickle.dump(variable, handle)

def open_pickle(path_to_file):
    with open(path_to_file, 'rb') as handle:
        f = pickle.load(handle)
    return f

class Caching:
    def __init__(self):
        self.access_list = [
        'account_data',
        'master_table',
        'team_list',
        'team_info',
        'player_price_data',
        'player_stats_data',
        'team_ids',
        'username_hash',
        ]

    @staticmethod
    def get_cached_data(fname):
        return open_pickle('./data/' + fname + '.pickle')

    def cache_data(self, fname):
        out = {}
        for d in self.access_list:
            out[d] = getattr(self, d)
        save_to_pickle(out, './data/' + fname + '.pickle')