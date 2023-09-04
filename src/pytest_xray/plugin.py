import base64
from pathlib import Path
from typing import Callable, Tuple, Union, overload

import pytest
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
    XRAY_ADD_CAPTURES,
    XRAY_ALLOW_DUPLICATE_IDS,
    XRAY_EXECUTION_ID,
    XRAY_PLUGIN,
    XRAY_TEST_PLAN_ID,
    XRAYPATH,
)
from pytest_xray.exceptions import XrayError
from pytest_xray.file_publisher import FilePublisher
from pytest_xray.helper import get_api_key_auth, get_basic_auth, get_bearer_auth
from pytest_xray.xray_plugin import XrayPlugin, evidences
from pytest_xray.xray_publisher import ApiKeyAuth, ClientSecretAuth, XrayPublisher


def pytest_addoption(parser: Parser):
    xray = parser.getgroup('Jira Xray report')
    xray.addoption(
        JIRA_XRAY_FLAG,
        action='store_true',
        default=False,
        help='Upload test results to JIRA XRAY'
    )
    xray.addoption(
        JIRA_CLOUD,
        action='store_true',
        default=False,
        help='Use with JIRA XRAY cloud server'
    )
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
        XRAY_EXECUTION_ID,
        action='store',
        metavar='ExecutionId',
        default=None,
        help='XRAY Test Execution ID'
    )
    xray.addoption(
        XRAY_TEST_PLAN_ID,
        action='store',
        metavar='TestplanId',
        default=None,
        help='XRAY Test Plan ID'
    )
    xray.addoption(
        XRAYPATH,
        action='store',
        metavar='path',
        default=None,
        help='Do not upload to a server but create JSON report file at given path'
    )
    xray.addoption(
        XRAY_ALLOW_DUPLICATE_IDS,
        action='store_true',
        default=False,
        help='Allow test ids to be present on multiple pytest tests'
    )
    xray.addoption(
        XRAY_ADD_CAPTURES,
        action='store_true',
        default=False,
        help='Add captures from log, stdout or/and stderr, to the report comment field'
    )


def pytest_addhooks(pluginmanager):
    pluginmanager.add_hookspecs(hooks)


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        'markers', 'xray(JIRA_ID): mark test with JIRA XRAY test case ID'
    )
    if config.option.collectonly:
        return

    if not config.getoption(JIRA_XRAY_FLAG):
        return

    xray_path = config.getoption(XRAYPATH)

    if xray_path:
        publisher = FilePublisher(xray_path)  # type: ignore
    else:
        if config.getoption(JIRA_CLOUD):
            endpoint = TEST_EXECUTION_ENDPOINT_CLOUD
        else:
            endpoint = TEST_EXECUTION_ENDPOINT

        if config.getoption(JIRA_CLIENT_SECRET_AUTH):
            options = get_bearer_auth()
            auth: Union[AuthBase, Tuple[str, str]] = ClientSecretAuth(
                options['BASE_URL'],
                options['CLIENT_ID'],
                options['CLIENT_SECRET'],
                options['VERIFY']
            )
        elif config.getoption(JIRA_API_KEY):
            options = get_api_key_auth()
            auth = ApiKeyAuth(options['API_KEY'])
        else:
            options = get_basic_auth()
            auth = (options['USER'], options['PASSWORD'])

        publisher = XrayPublisher(  # type: ignore
            base_url=options['BASE_URL'],
            endpoint=endpoint,
            auth=auth,
            verify=options['VERIFY']
        )

    plugin = XrayPlugin(config, publisher)
    config.pluginmanager.register(plugin=plugin, name=XRAY_PLUGIN)


evidence_nb: int = 1


@pytest.fixture
def evidence(request) -> Callable:
    """ Fixture to add an evidence to the Test Run details of a Test.
    See https://docs.getxray.app/display/XRAY/Import+Execution+Results

    Copyright © 2023 Orange - All rights reserved
    """
    media_types = {
        'bin': 'application/octet-stream',
        'csv': 'text/csv',
        'gz': 'application/gzip',
        'html': 'text/html',
        'json': 'application/json',
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'js': 'text/javascript',
        'md': 'text/markdown',
        'pcap': 'application/vnd.tcdump.pcap',
        'png': 'image/png',
        'spdx': 'text/spdx',
        'txt': 'text/plain',
        'xml': 'text/xml',
        'yml': 'application/yaml',
        'yaml': 'application/yaml',
        'zip': 'application/zip'
    }

    @overload
    def wrapper_evidence(path: str, *, data: bytes, ctype: str) -> None:
        pass

    @overload
    def wrapper_evidence(path: str, *, data: str, ctype: str) -> None:
        pass

    def wrapper_evidence(path='', *, data='', ctype='') -> None:
        """
        Behaviour of the fixture from the value of 'path', 'data' and 'ctype'
        arguments:
+------+------+-------+--------------------------------------------------------+
| path | data | ctype | Comment                                                |
+======+======+=======+========================================================+
| No   | No   | No    | Error, "No data to upload"                             |
+------+------+-------+--------------------------------------------------------+
| No   | No   | Yes   | Error, "No data to upload"                             |
+------+------+-------+--------------------------------------------------------+
| No   | Yes  | No    | If data is binary, content-type is "application/octet- |
|      |      |       | stream" otherwise "text/plain". For filename see below.|
+------+------+-------+--------------------------------------------------------+
| No   | Yes  | Yes   | Filename is set to "attachmentX.Y" where X is a number |
|      |      |       | and extension Y is deduced from content-type value.    |
+------+------+-------+--------------------------------------------------------+
| Yes  | Yes  | Yes   | Takes all the values given.                            |
+------+------+-------+--------------------------------------------------------+
| Yes  | Yes  | No    | Content-type is set from the filename extension.       |
+------+------+-------+--------------------------------------------------------+
| Yes  | No   | Yes   | Data is the content of the file.                       |
+------+------+-------+--------------------------------------------------------+
| Yes  | No   | No    | Extension of filename is used to determine content-type|
|      |      |       | and content of file is the data.                       |
+------+------+-------+--------------------------------------------------------+
        """
        global evidence_nb
        # data_base64: str = ''
        # evidence_name: str = ''
        # contentType: str = ''

        if path == '':
            if data == '':
                raise XrayError('No data to upload')
            elif isinstance(data, bytes):
                db64 = base64.b64encode(data)
            else:
                db64 = base64.b64encode(bytes(data, 'utf-8'))
            data_base64 = db64.decode('utf-8')

            if ctype == '':
                if isinstance(data, bytes):
                    contentType = 'application/octet-stream'
                else:
                    contentType = 'text/plain'
            else:
                contentType = ctype

            evidence_name = 'attachment' + str(evidence_nb)
            extension: str = ''
            for e, t in media_types.items():
                if t == contentType:
                    extension = e
                    break
            if extension != '':
                evidence_name += '.' + extension
                # else: no extension
            evidence_nb += 1

        else:
            if not isinstance(path, str):
                raise XrayError('Path must be a string')
            evidence_path: Path = Path(path)
            # Jira wants non absolute pathname as filename attachment
            evidence_name = evidence_path.name

            if data == '':
                if not evidence_path.is_absolute():
                    evidence_path = request.path.parent.joinpath(evidence_path)
                try:
                    with open(evidence_path, 'rb') as f:
                        data_base64 = base64.b64encode(f.read()).decode('utf-8')
                except OSError:
                    raise XrayError(f'Cannot open or read file {evidence_path}')
            elif isinstance(data, bytes):
                data_base64 = base64.b64encode(data).decode('utf-8')
            else:
                data_base64 = base64.b64encode(bytes(data, encoding='utf-8')).decode('utf-8')

            if ctype == '':
                extension = evidence_path.suffix.replace('.', '')
                if media_types.get(extension) is None:
                    raise XrayError(f'Media type not found for extension {extension}')
                else:
                    contentType = str(media_types.get(extension))
            else:
                contentType = ctype

        new_evidence = {
            'data': data_base64,
            'filename': evidence_name,
            'contentType': contentType
        }
        # Add the new evidence to the stash of the node to get it from the hook function
        if request.node.stash.__contains__(evidences):
            request.node.stash[evidences].append(new_evidence)
        else:
            request.node.stash[evidences] = [new_evidence]

    return wrapper_evidence
