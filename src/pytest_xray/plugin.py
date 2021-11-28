import os
from pathlib import Path
from typing import List, Tuple, Union, Optional, Dict

from _pytest.config import Config, ExitCode
from _pytest.config.argparsing import Parser
from _pytest.mark import Mark
from _pytest.nodes import Item
from _pytest.terminal import TerminalReporter
from requests.auth import AuthBase

from pytest_xray.constant import (
    JIRA_XRAY_FLAG,
    XRAY_PLUGIN,
    XRAY_TEST_PLAN_ID,
    XRAY_EXECUTION_ID,
    JIRA_CLOUD,
    XRAYPATH,
    XRAY_MARKER_NAME
)
from pytest_xray.exceptions import XrayError
from pytest_xray.file_publisher import FilePublisher
from pytest_xray.helper import (
    Status,
    TestCase,
    TestExecution,
    StatusBuilder,
    CloudStatus,
    get_bearer_auth,
    get_basic_auth,
)
from pytest_xray.xray_publisher import BearerAuth, XrayPublisher


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


def pytest_configure(config: Config) -> None:
    if not config.getoption(JIRA_XRAY_FLAG):
        return

    xray_path = config.getoption(XRAYPATH)

    if xray_path:
        publisher = FilePublisher(xray_path)  # type: ignore
    else:
        if config.getoption(JIRA_CLOUD):
            options = get_bearer_auth()
            auth: Union[AuthBase, Tuple[str, str]] = BearerAuth(
                options['BASE_URL'],
                options['CLIENT_ID'],
                options['CLIENT_SECRET']
            )
        else:
            options = get_basic_auth()
            auth = (options['USER'], options['PASSWORD'])

        publisher = XrayPublisher(  # type: ignore
            base_url=options['BASE_URL'],
            auth=auth,
            verify=options['VERIFY']
        )

    plugin = XrayPlugin(config, publisher)
    config.pluginmanager.register(plugin=plugin, name=XRAY_PLUGIN)
    config.addinivalue_line(
        'markers', 'xray(JIRA_ID): mark test with JIRA XRAY test case ID'
    )


class XrayPlugin:

    def __init__(self, config, publisher):
        self.config = config
        self.publisher = publisher
        self.test_execution_id: str = self.config.getoption(XRAY_EXECUTION_ID)
        self.test_plan_id: str = self.config.getoption(XRAY_TEST_PLAN_ID)
        self.is_cloud_server: str = self.config.getoption(JIRA_CLOUD)
        logfile = self.config.getoption(XRAYPATH)
        self.logfile: str = self._get_normalize_logfile(logfile) if logfile else None
        self.test_keys: Dict[str, str] = {}  # store nodeid and TestId
        self.test_execution: TestExecution = TestExecution(
            test_execution_key=self.test_execution_id,
            test_plan_key=self.test_plan_id
        )
        if self.is_cloud_server:
            self.status_builder: StatusBuilder = StatusBuilder(CloudStatus)
        else:
            self.status_builder: StatusBuilder = StatusBuilder(Status)

    @staticmethod
    def _get_normalize_logfile(logfile: str) -> str:
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        logfile = os.path.normpath(os.path.abspath(logfile))
        os.makedirs(os.path.dirname(logfile), exist_ok=True)
        return logfile

    def _associate_marker_metadata_for(self, items: List[Item]) -> None:
        """Store XRAY test id for test item."""
        test_ids = []
        duplicated_ids = []

        for item in items:
            marker = self._get_xray_marker(item)
            if not marker:
                continue

            test_key = marker.args[0]
            if test_key in test_ids:
                duplicated_ids.append(test_key)
            else:
                test_ids.append(test_key)
            self.test_keys[item.nodeid] = test_key
            if duplicated_ids:
                raise XrayError(f'Duplicated test case ids: {duplicated_ids}')

    def _get_test_key_for(self, item: Item) -> Optional[str]:
        """Return XRAY test id for item."""
        test_id = self.test_keys.get(item.nodeid)
        if test_id:
            return test_id
        return None

    @staticmethod
    def _get_xray_marker(item: Item) -> Optional[Mark]:
        return item.get_closest_marker(XRAY_MARKER_NAME)

    def _append_test(self, item: Item, status: str) -> None:
        test_key = self._get_test_key_for(item)
        if test_key:
            tc = TestCase(test_key, self.status_builder(status), item.longreprtext)
            self.test_execution.append(tc)

    def pytest_collection_modifyitems(self, config: Config, items: List[Item]) -> None:
        self._associate_marker_metadata_for(items)

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter, exitstatus: ExitCode, config: Config) -> None:
        stats = terminalreporter.stats
        if 'passed' in stats:
            for item in stats['passed']:
                self._append_test(item, 'PASS')
        if 'xpassed' in stats:
            for item in stats['xpassed']:
                self._append_test(item, 'PASS')
        if 'failed' in stats:
            for item in stats['failed']:
                self._append_test(item, 'FAIL')
        if 'xfailed' in stats:
            for item in stats['xfailed']:
                self._append_test(item, 'FAIL')
        if 'error' in stats:
            for item in stats['error']:
                self._append_test(item, 'FAIL')
        if 'skipped' in stats:
            for item in stats['skipped']:
                self._append_test(item, 'ABORTED')

        try:
            issue_id = self.publisher.publish(self.test_execution.as_dict())
        except XrayError as exc:
            terminalreporter.ensure_newline()
            terminalreporter.section('Jira XRAY', sep='-', red=True, bold=True)
            terminalreporter.write_line('Could not publish results to Jira XRAY!')
            if exc.message:
                terminalreporter.write_line(exc.message)
        else:
            if issue_id and self.logfile:
                terminalreporter.write_sep(
                    '-', f'Generated XRAY execution report file: {Path(issue_id).absolute()}'
                )
            elif issue_id:
                terminalreporter.write_sep(
                    '-', f'Uploaded results to JIRA XRAY. Test Execution Id: {issue_id}'
                )
