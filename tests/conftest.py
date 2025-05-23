import pytest
from pytest_httpserver import HTTPServer

from pytest_xray.constant import (
    AUTHENTICATE_ENDPOINT,
    TEST_EXECUTION_ENDPOINT,
    TEST_EXECUTION_ENDPOINT_CLOUD,
)


pytest_plugins = ['pytester']


@pytest.fixture
def environment_variables(monkeypatch):
    monkeypatch.setenv('XRAY_API_BASE_URL', 'http://127.0.0.1:5002')
    monkeypatch.setenv('XRAY_API_USER', 'jirauser')
    monkeypatch.setenv('XRAY_API_PASSWORD', 'jirapassword')
    monkeypatch.setenv('XRAY_CLIENT_ID', 'client_id')
    monkeypatch.setenv('XRAY_CLIENT_SECRET', 'client_secret')
    monkeypatch.setenv('XRAY_API_TOKEN', 'token')
    monkeypatch.setenv('XRAY_API_KEY', 'api_key')


@pytest.fixture(scope='session')
def httpserver_listen_address():
    return '127.0.0.1', 5002


@pytest.fixture
def fake_xray_server(httpserver: HTTPServer, environment_variables):
    """Create fake Jira XRAY server."""
    httpserver.expect_request(TEST_EXECUTION_ENDPOINT, method='POST').respond_with_json(
        {'testExecIssue': {'key': '1000'}})
    # cloud server
    httpserver.expect_request(TEST_EXECUTION_ENDPOINT_CLOUD, method='POST').respond_with_json({'key': '1000'})
    httpserver.expect_request(AUTHENTICATE_ENDPOINT, 'POST').respond_with_data('dummy_token')
