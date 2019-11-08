import json
from FPLManager.player_stats_url import stats_url, top_50_url


class PriceData:

    def __init__(self, web_object):
        print('Getting player price change data...')
        self.web_object = web_object
        self.price_data_url = self.find_price_data_url()
        self.player_price_data = self.get_player_price_data()
        self.player_stats_data = self.get_player_stats_data()
        self.player_top_50_data = self.get_top_50_data()

    def find_price_data_url(self):
        self.web_object.driver.get('http://www.fplstatistics.co.uk/')
        browser_log = self.web_object.driver.get_log('performance')
        events = [json.loads(entry['message'])['message'] for entry in browser_log]
        events = [event for event in events if 'Network.response' in event['method']]

        for event in events:
            if 'response' in event['params']:
                if 'http://www.fplstatistics.co.uk/Home/AjaxPrices' in event['params']['response']['url']:
                    return event['params']['response']['url']

    def get_player_stats_data(self):
        return json.loads(self.web_object.session.get(stats_url).text)['aaData']

    def get_top_50_data(self):
        return json.loads(self.web_object.session.get(top_50_url).text)['aaData']

    def get_player_price_data(self):
        return json.loads(self.web_object.session.get(self.price_data_url).text)['aaData']
