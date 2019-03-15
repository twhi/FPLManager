import requests
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options


class WebStuff:
    def __init__(self, username, password):
        print('Firing up Selenium browser and requests session...')

        self.login_status = None

        # do requests stuff
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.payload = self.construct_fpl_session_payload()

        # do selenium stuff
        self.driver = self.initialise_selenium()

    def construct_fpl_session_payload(self):
        url_home = 'https://fantasy.premierleague.com/'
        self.session.get(url_home)
        csrftoken = self.session.cookies['csrftoken']
        return {
            'csrfmiddlewaretoken': csrftoken,
            'login': self.username,
            'password': self.password,
            'app': 'plfpl-web',
            'redirect_uri': 'https://fantasy.premierleague.com/a/login'
        }

    def log_into_fpl(self):
        login_url = 'https://users.premierleague.com/accounts/login/'
        self.login_status = self.session.post(login_url, data=self.payload)


    def log_out_of_fpl(self):
        logout_url = 'https://users.premierleague.com/accounts/logout/?redirect_uri=https://fantasy.premierleague.com/&app=plfpl-web'
        status = self.session.post(logout_url, data=self.payload)
        return status

    @staticmethod
    def initialise_selenium():
        caps = DesiredCapabilities.CHROME
        caps['loggingPrefs'] = {'performance': 'ALL'}
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        d = webdriver.Chrome(chrome_options=chrome_options, desired_capabilities=caps)
        return d
