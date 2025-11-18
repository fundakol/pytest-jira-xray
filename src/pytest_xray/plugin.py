import os
from typing import Union

from _pytest.config import Config
from _pytest.config.argparsing import Parser
from requests.auth import AuthBase

from pytest_xray import hooks
from pytest_xray.constant import (
    JIRA_API_KEY,
    JIRA_CLIENT_SECRET_AUTH,
    JIRA_CLOUD,
    JIRA_XRAY_FLAG,
    TEST_EXECUTION_ENDPOINT,
    TEST_EXECUTION_ENDPOINT_CLOUD,
    TEST_EXECUTION_ENDPOINT_MULTIPART,
    TEST_EXECUTION_ENDPOINT_CLOUD_MULTIPART,
    ENV_TEST_EXECUTION_FIELDS,
    XRAY_ADD_CAPTURES,
    XRAY_ALLOW_DUPLICATE_IDS,
    XRAY_EXECUTION_ID,
    XRAY_PLUGIN,
    XRAY_TEST_PLAN_ID,
    XRAYPATH,
)
from pytest_xray.file_publisher import FilePublisher
from pytest_xray.helper import get_api_key_auth, get_basic_auth, get_bearer_auth
from pytest_xray.xray_plugin import XrayPlugin
from pytest_xray.xray_publisher import ApiKeyAuth, ClientSecretAuth, XrayPublisher

def pytest_addoption(parser: Parser):
    xray = parser.getgroup('Jira Xray report')
    xray.addoption(JIRA_XRAY_FLAG, action='store_true', default=False, help='Upload test results to JIRA XRAY')
    xray.addoption(JIRA_CLOUD, action='store_true', default=False, help='Use with JIRA XRAY cloud server')
    xray.addoption(
        JIRA_API_KEY,
        action='store_true',
        default=False,
        help='Use Jira API Key authentication',
    )
    xray.addoption(
        JIRA_CLIENT_SECRET_AUTH,
        action='store_true',
        default=False,
        help='Use client secret authentication',
    )
    xray.addoption(
        XRAY_EXECUTION_ID, action='store', metavar='ExecutionId', default=None, help='XRAY Test Execution ID'
    )
    xray.addoption(XRAY_TEST_PLAN_ID, action='store', metavar='TestplanId', default=None, help='XRAY Test Plan ID')
    xray.addoption(
        XRAYPATH,
        action='store',
        metavar='path',
        default=None,
        help='Do not upload to a server but create JSON report file at given path',
    )
    xray.addoption(
        XRAY_ALLOW_DUPLICATE_IDS,
        action='store_true',
        default=False,
        help='Allow test ids to be present on multiple pytest tests',
    )
    xray.addoption(
        XRAY_ADD_CAPTURES,
        action='store_true',
        default=False,
        help='Add captures from log, stdout or/and stderr, to the report comment field',
    )


def pytest_addhooks(pluginmanager):
    pluginmanager.add_hookspecs(hooks)


def pytest_configure(config: Config) -> None:
    config.addinivalue_line('markers', 'xray(JIRA_ID): mark test with JIRA XRAY test case ID')
    if config.option.collectonly:
        return

    if not config.getoption(JIRA_XRAY_FLAG):
        return

    xray_path = config.getoption(XRAYPATH)

    if xray_path:
        publisher = FilePublisher(xray_path)  # type: ignore
    else:
        use_cloud = config.getoption(JIRA_CLOUD)
        endpoint = TEST_EXECUTION_ENDPOINT_CLOUD if use_cloud else TEST_EXECUTION_ENDPOINT
        multipart_endpoint = (TEST_EXECUTION_ENDPOINT_CLOUD_MULTIPART if use_cloud else TEST_EXECUTION_ENDPOINT_MULTIPART)

        if config.getoption(JIRA_CLIENT_SECRET_AUTH):
            options = get_bearer_auth()
            auth: Union[AuthBase, tuple[str, str]] = ClientSecretAuth(
                options['BASE_URL'], options['CLIENT_ID'], options['CLIENT_SECRET'], options['VERIFY']
            )
        elif config.getoption(JIRA_API_KEY):
            options = get_api_key_auth()
            auth = ApiKeyAuth(options['API_KEY'])
        else:
            options = get_basic_auth()
            auth = (options['USER'], options['PASSWORD'])

        publisher = XrayPublisher(  # type: ignore
            base_url=options['BASE_URL'], endpoint=endpoint, auth=auth, verify=options['VERIFY']
        )

    plugin = XrayPlugin(config, publisher)
    
    if os.getenv("XRAY_EXECUTION_FIELDS"):
        base_url = getattr(publisher, "base_url", None)
        multipart_path = getattr(plugin, "_MULTIPART_ENDPOINT_PATH", "/api/internal/import/execution/multipart")
        if base_url:
            plugin._multipart_endpoint = base_url + multipart_path
        else:
            # No base_url => file publisher or unsupported transport. Avoid crashing.
            plugin._multipart_endpoint = None
            log.debug("XRAY: multipart disabled (publisher has no base_url).")
    else:
        plugin._multipart_endpoint = None
    plugin._custom_fields_env = os.environ.get(ENV_TEST_EXECUTION_FIELDS)
    config.pluginmanager.register(plugin=plugin, name=XRAY_PLUGIN)
