import requests


class RequestsSession:
    def __init__(self, username, password):
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.payload = self.construct_fpl_session_payload()

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