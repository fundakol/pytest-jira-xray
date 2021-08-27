import pytest

from .mock_server import MockServer


@pytest.fixture(scope="session", autouse=True)
def http_server():
    server = MockServer(5002)
    server.add_json_response('/rest/raven/2.0/import/execution',
                             {'testExecIssue': {'key': '1000'}},
                             methods=('POST',))
    server.add_callback_response('/api/v2/authenticate',
                                 lambda: 'token',
                                 methods=('POST',))
    server.start()
    yield
    server.shutdown_server()
