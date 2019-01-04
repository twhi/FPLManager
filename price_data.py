import json

from selenium_session import SeleniumSession


class PriceData(SeleniumSession):

    def __init__(self, web_object):
        super().__init__(web_object)
        self.web_object = web_object
        self.price_data_url = self.find_price_data_url()
        self.player_price_data = self.get_player_price_data()

    def find_price_data_url(self):
        self.web_object.driver.get('http://www.fplstatistics.co.uk/')
        browser_log = self.web_object.driver.get_log('performance')
        events = [json.loads(entry['message'])['message'] for entry in browser_log]
        events = [event for event in events if 'Network.response' in event['method']]

        for event in events:
            if 'http://www.fplstatistics.co.uk/Home/AjaxPrices' in event['params']['response']['url']:
                return event['params']['response']['url']

    def get_player_price_data(self):
        return json.loads(self.web_object.session.get(self.price_data_url).text)['aaData']