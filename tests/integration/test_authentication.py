from tests.integration.scaffold import MyTestCase
import requests


class TestAuthentication(MyTestCase):
    def setUp(self):
        super().setUp()

    def test_admin_login(self):
        url = self.base_url.format('authenticate')
        payload = {
            "data": {
                "user": "admin",
                "password": "password"
            }
        }
        r = requests.post(url, json=payload)
        r_payload = r.json()
        r_cookies = r.cookies
        self.assertEqual(r.status_code, 201)
        self.assertIsInstance(r_payload['data']['id'], str)
        self.assertIsInstance(r_cookies['DEPLOYER_SESSION'], str)
        self.assertEqual(r_cookies['DEPLOYER_SESSION'], r_payload['data']['id'])
        self.logout(r_cookies)

    def test_admin_login_invalid_login(self):
        url = self.base_url.format('authenticate')
        payload = {
            "data": {
                "user": "admin",
                "password": "passwordd"
            }
        }
        r = requests.post(url, json=payload)
        r_payload = r.json()
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r_payload['errors'][0]['id'], 1001)

    def test_admin_login_invalid_payload(self):
        url = self.base_url.format('authenticate')
        payload = {
            "data": {
                "userr": "admin",
                "password": "password"
            }
        }
        r = requests.post(url, json=payload)
        r_payload = r.json()
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r_payload['errors'][0]['id'], 3001)

    def test_admin_logout(self):
        url = self.base_url.format('authenticate')
        session = self.login('admin', 'password')
        r = requests.delete(url, cookies=session)
        self.assertEqual(r.status_code, 204)
