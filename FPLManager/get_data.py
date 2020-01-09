import os.path
import time
import hashlib

from process import ProcessData
from web_stuff import WebStuff
from caching import Caching


class GetData(Caching):

    def __init__(self, u, p, reduce, refresh):
        self.username = u
        self.username_hash = hashlib.md5(self.username.encode('utf-8')).hexdigest()
        self.password = p
        self.reduce = reduce
        self.refresh = refresh
        self.data = self.get_data()

    @staticmethod
    def older_than_one_hour(file):
        current_time = time.time()
        last_modified_time = os.path.getmtime(file)
        if (current_time - last_modified_time) > (60 * 60):
            return True
        else:
            return False

    def use_cached_data(self):
        Caching.__init__(self)
        data = self.get_cached_data(self.username_hash)
        return ProcessData(self.reduce, **data)

    def user_data_exists(self):
        file_list_raw = os.listdir('./data')
        file_list = [os.path.splitext(file)[0] for file in file_list_raw]
        if self.username_hash in file_list:
            return True
        return False

    def get_data_from_web(self):
        # check if credentials were supplied
        if not self.username or not self.password:
            print('\nProcess failed. Incomplete credentials supplied.')
            exit()

        # initialise selenium and requests session
        web = WebStuff(self.username, self.password)

        # attempt to log in, don't give up until logged in (stupid work network...)
        logged_in = False
        while not logged_in:
            try:
                web.log_into_fpl()
                logged_in = True
                print('Logged in successfully!')
            except:
                print('Failed to log in, retrying...')
        return ProcessData(self.reduce, self.username_hash, web_session=web)

    def get_data(self):
        try:
            need_new_data = self.older_than_one_hour('./data/' + self.username_hash + '.pickle')
        except:
            # no data exists
            return self.get_data_from_web()

        # data exists
        if need_new_data or self.refresh or not self.user_data_exists():
            return self.get_data_from_web()
        else:
            return self.use_cached_data()
