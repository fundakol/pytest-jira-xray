import pytest

from .mock_server import MockServer


pytest_plugins = ['pytester']


@pytest.fixture(scope='function')
def mocked_environ(monkeypatch):
    monkeypatch.setenv('XRAY_API_BASE_URL', 'http://127.0.0.1:5002')
    monkeypatch.setenv('XRAY_API_USER', 'jira_user')
    monkeypatch.setenv('XRAY_API_PASSWORD', 'jira_password')
    monkeypatch.setenv('XRAY_CLIENT_ID', 'client_id')
    monkeypatch.setenv('XRAY_CLIENT_SECRET', 'client_secret')
    monkeypatch.setenv('XRAY_API_TOKEN', 'token')
    monkeypatch.setenv('XRAY_API_KEY', 'api_key')


@pytest.fixture(scope='module')
def http_server():
    server = MockServer(5002)
    server.add_json_response(
        '/rest/raven/2.0/import/execution',
        {'testExecIssue': {'key': '1000'}},
        methods=('POST',)
    )
    # cloud
    server.add_json_response(
        '/api/v2/import/execution',
        {'key': '1000'},
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
