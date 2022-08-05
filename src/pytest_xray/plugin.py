import datetime as dt
import os
from pathlib import Path
from typing import List, Tuple, Union, Optional, Dict

import pytest
from _pytest.config import Config, ExitCode
from _pytest.config.argparsing import Parser
from _pytest.mark import Mark
from _pytest.nodes import Item
from _pytest.reports import TestReport
from _pytest.terminal import TerminalReporter
from requests.auth import AuthBase

from pytest_xray.constant import (
    JIRA_XRAY_FLAG,
    XRAY_PLUGIN,
    XRAY_TEST_PLAN_ID,
    XRAY_EXECUTION_ID,
    JIRA_CLOUD,
    JIRA_API_KEY,
    JIRA_TOKEN,
    JIRA_CLIENT_SECRET_AUTH,
    XRAYPATH,
    XRAY_MARKER_NAME,
    TEST_EXECUTION_ENDPOINT,
    TEST_EXECUTION_ENDPOINT_CLOUD,
    XRAY_ALLOW_DUPLICATE_IDS
)
from pytest_xray.exceptions import XrayError
from pytest_xray.file_publisher import FilePublisher
from pytest_xray.helper import (
    Status,
    TestCase,
    TestExecution,
    STATUS_STR_MAPPER_JIRA,
    STATUS_STR_MAPPER_CLOUD,
    get_bearer_auth,
    get_api_key_auth,
    get_basic_auth, get_api_token_auth,
)
from pytest_xray import hooks
from pytest_xray.xray_publisher import (
    ClientSecretAuth,
    ApiKeyAuth,
    XrayPublisher,
    TokenAuth
)


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
        help='Use with JIRA XRAY could server'
    )
    xray.addoption(
        JIRA_API_KEY,
        action='store_true',
        default=False,
        help='Use API Key authentication',
    )
    xray.addoption(
        JIRA_TOKEN,
        action='store_true',
        default=False,
        help='Use token authentication',
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


def pytest_addhooks(pluginmanager):
    pluginmanager.add_hookspecs(hooks)


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        'markers', 'xray(JIRA_ID): mark test with JIRA XRAY test case ID'
    )

    if not config.getoption(JIRA_XRAY_FLAG) or hasattr(config, 'workerinput'):
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
                options['CLIENT_SECRET']
            )
        elif config.getoption(JIRA_API_KEY):
            options = get_api_key_auth()
            auth = ApiKeyAuth(options['API_KEY'])
        elif config.getoption(JIRA_TOKEN):
            options = get_api_token_auth()
            auth = TokenAuth(options['TOKEN'])
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


class XrayPlugin:

    def __init__(self, config, publisher):
        self.config = config
        self.publisher = publisher
        self.test_execution_id: str = self.config.getoption(XRAY_EXECUTION_ID)
        self.test_plan_id: str = self.config.getoption(XRAY_TEST_PLAN_ID)
        self.is_cloud_server: str = self.config.getoption(JIRA_CLOUD)
        self.allow_duplicate_ids: bool = self.config.getoption(
            XRAY_ALLOW_DUPLICATE_IDS
        )
        logfile = self.config.getoption(XRAYPATH)
        self.logfile: str = self._get_normalize_logfile(logfile) if logfile else None
        self.test_keys: Dict[str, List[str]] = {}  # store nodeid and TestId
        self.issue_id = None
        self.exception = None
        self.test_execution: TestExecution = TestExecution(
            test_execution_key=self.test_execution_id,
            test_plan_key=self.test_plan_id
        )
        self.status_str_mapper = STATUS_STR_MAPPER_JIRA
        if self.is_cloud_server:
            self.status_str_mapper = STATUS_STR_MAPPER_CLOUD

    @staticmethod
    def _get_normalize_logfile(logfile: str) -> str:
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        logfile = os.path.normpath(os.path.abspath(logfile))
        return logfile

    def _associate_marker_metadata_for(self, items: List[Item]) -> None:
        """Store XRAY test id for test item."""
        jira_ids: List[str] = []
        duplicated_jira_ids: List[str] = []

        for item in items:
            marker = self._get_xray_marker(item)
            if not marker:
                continue

            test_keys: List[str]
            if isinstance(marker.args[0], str):
                test_keys = [marker.args[0]]
            elif isinstance(marker.args[0], list):
                test_keys = list(marker.args[0])
            else:
                raise XrayError('xray marker can only accept strings or lists')

            for test_key in test_keys:
                if test_key in jira_ids:
                    duplicated_jira_ids.append(test_key)
                else:
                    jira_ids.append(test_key)

            self.test_keys[item.nodeid] = test_keys

            if duplicated_jira_ids and not self.allow_duplicate_ids:
                raise XrayError(f'Duplicated test case ids: {duplicated_jira_ids}')

    def _get_test_keys_for(self, nodeid: str) -> Optional[List[str]]:
        """Return XRAY test id for nodeid."""
        return self.test_keys.get(nodeid)

    @staticmethod
    def _get_xray_marker(item: Item) -> Optional[Mark]:
        return item.get_closest_marker(XRAY_MARKER_NAME)

    def pytest_sessionstart(self, session):
        self.test_execution.start_date = dt.datetime.now(tz=dt.timezone.utc)

    def pytest_runtest_logreport(self, report: TestReport):
        status = self._get_status_from_report(report)
        if status is None:
            return

        test_keys = self._get_test_keys_for(report.nodeid)
        if test_keys is None:
            return

        for test_key in test_keys:
            new_test_case = TestCase(
                test_key=test_key,
                status=status,
                comment=report.longreprtext,
                status_str_mapper=self.status_str_mapper
            )
            try:
                test_case = self.test_execution.find_test_case(test_key)
            except KeyError:
                self.test_execution.append(new_test_case)
            else:
                test_case.merge(new_test_case)

    def _get_status_from_report(self, report) -> Optional[Status]:
        if report.failed:
            if report.when != 'call':
                return Status.FAIL
            elif hasattr(report, 'wasxfail'):
                return Status.PASS
            else:
                return Status.FAIL
        elif report.skipped:
            if hasattr(report, 'wasxfail'):
                return Status.FAIL
            else:
                return Status.ABORTED
        elif report.passed and report.when == 'call':
            return Status.PASS

        return None

    def pytest_collection_modifyitems(self, config: Config, items: List[Item]) -> None:
        self._associate_marker_metadata_for(items)

    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        results = self.test_execution.as_dict()
        session.config.pluginmanager.hook.pytest_xray_results(
            results=results, session=session
        )
        self.test_execution.finish_date = dt.datetime.now(tz=dt.timezone.utc)
        try:
            self.issue_id = self.publisher.publish(results)
        except XrayError as exc:
            self.exception = exc

    def pytest_terminal_summary(
        self, terminalreporter: TerminalReporter, exitstatus: ExitCode, config: Config
    ) -> None:
        if self.exception:
            terminalreporter.ensure_newline()
            terminalreporter.section('Jira XRAY', sep='-', red=True, bold=True)
            terminalreporter.write_line('Could not publish results to Jira XRAY!')
            if self.exception.message:
                terminalreporter.write_line(self.exception.message)
        else:
            if self.issue_id and self.logfile:
                terminalreporter.write_sep(
                    '-', f'Generated XRAY execution report file: {Path(self.logfile).absolute()}'
                )
            elif self.issue_id:
                terminalreporter.write_sep(
                    '-', f'Uploaded results to JIRA XRAY. Test Execution Id: {self.issue_id}'
                )
