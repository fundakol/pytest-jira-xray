import os

import pytest

from .mock_server import MockServer

pytest_plugins = ['pytester']


@pytest.fixture(scope='session')
def environment_variables():
    os.environ['XRAY_API_BASE_URL'] = 'http://127.0.0.1:5002'
    os.environ['XRAY_API_USER'] = 'jirauser'
    os.environ['XRAY_API_PASSWORD'] = 'jirapassword'
    os.environ['XRAY_CLIENT_ID'] = 'client_id'
    os.environ['XRAY_CLIENT_SECRET'] = 'client_secret'


@pytest.fixture(scope='session', autouse=True)
def http_server(environment_variables):
    server = MockServer(5002)
    server.add_json_response(
        '/rest/raven/2.0/import/execution',
        {'testExecIssue': {'key': '1000'}},
        methods=('POST',)
    )
    # cloud
    server.add_json_response(
        '/api/v2/import/execution',
        {'testExecIssue': {'key': '1000'}},
        methods=('POST',)
    )
    server.add_callback_response(
        '/api/v2/authenticate',
        lambda: 'token',
        methods=('POST',)
    )
    server.start()
    yield
    server.shutdown_server()
