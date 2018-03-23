import json
import unittest
from chalice.config import Config
from chalice.local import LocalGateway
from app import app


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.localGateway = LocalGateway(app, Config())

    def test_index(self):
        gateway = self.localGateway
        response = gateway.handle_request(method='GET',
                                          path='/',
                                          headers={},
                                          body='')
        assert response['statusCode'] == 200
        assert json.loads(response['body']) == dict([('hello', 'world')])

    def test_hello(self):
        gateway = self.localGateway
        response = gateway.handle_request(method='GET',
                                          path='/hello/alice',
                                          headers={},
                                          body='')
        assert response['statusCode'] == 200
        assert json.loads(response['body']) == dict([('hello', 'alice')])

    def test_users(self):
        gateway = self.localGateway
        response = gateway.handle_request(method='POST',
                                          path='/users',
                                          headers={'Content-Type':
                                                   'application/json'},
                                          body='["alice","bob"]')
        assert response['statusCode'] == 200
        expected = json.loads('{"user":["alice","bob"]}')
        actual = json.loads(response['body'])
        assert actual == expected

    @unittest.expectedFailure
    def test_invalid_path(self):
        gateway = self.localGateway
        response = gateway.handle_request(method='GET',
                                          path='/fake/path',
                                          headers={},
                                          body='')
        assert response['statusCode'] == 200

    def test_invalid_method(self):
        gateway = self.localGateway
        response = gateway.handle_request(method='POST',
                                          path='/',
                                          headers={},
                                          body='')
        assert response['statusCode'] == 405


if __name__ == '__main__':
    unittest.main()
