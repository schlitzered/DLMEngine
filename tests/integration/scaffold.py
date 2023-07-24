from unittest import TestCase

import requests


class MyTestCase(TestCase):
    def setUp(self):
        self.base_url = 'http://localhost:9000/api/v1/{0}'

    def login(self, username, password):
        url = self.base_url.format('authenticate')
        payload = {
            "data": {
                "user": username,
                "password": password
            }
        }
        r = requests.post(url, json=payload)
        return r.cookies

    def logout(self, session):
        url = self.base_url.format('authenticate')
        r = requests.delete(url, cookies=session)
