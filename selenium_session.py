from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options


class SeleniumSession:

    def __init__(self, web_object):
        web_object.driver = self.initialise_selenium()

    @staticmethod
    def initialise_selenium():
        caps = DesiredCapabilities.CHROME
        caps['loggingPrefs'] = {'performance': 'ALL'}
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        d = webdriver.Chrome(chrome_options=chrome_options, desired_capabilities=caps)
        return d