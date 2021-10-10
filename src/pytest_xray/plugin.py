from pathlib import Path
from typing import List

from _pytest.config import Config, ExitCode
from _pytest.config.argparsing import Parser
from _pytest.nodes import Item
from _pytest.terminal import TerminalReporter

from pytest_xray.constant import (
    JIRA_XRAY_FLAG,
    XRAY_PLUGIN,
    XRAY_TEST_PLAN_ID,
    XRAY_EXECUTION_ID,
    JIRA_CLOUD, XRAYPATH
)
from pytest_xray.exceptions import XrayError
from pytest_xray.file_publisher import FilePublisher
from pytest_xray.helper import (
    associate_marker_metadata_for,
    get_test_key_for,
    Status,
    TestCase,
    TestExecution,
    StatusBuilder,
    CloudStatus, get_bearer_auth, get_basic_auth
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
        default=None,
        help='XRAY Test Execution ID'
    )
    xray.addoption(
        XRAY_TEST_PLAN_ID,
        action='store',
        default=None,
        help='XRAY Test Plan ID'
    )
    xray.addoption(
        XRAYPATH,
        action='store',
        default=None,
        help='Do not upload to a server but create JSON report file at given path'
    )


def pytest_configure(config: Config) -> None:
    if not config.getoption(JIRA_XRAY_FLAG):
        return

    xray_path = config.getoption(XRAYPATH)

    if xray_path:
        plugin = FilePublisher(xray_path)
    else:
        if config.getoption(JIRA_CLOUD):
            options = get_bearer_auth()
            auth = BearerAuth(
                options['BASE_URL'],
                options['CLIENT_ID'],
                options['CLIENT_SECRET']
            )
        else:
            options = get_basic_auth()
            auth = (options['USER'], options['PASSWORD'])

        plugin = XrayPublisher(
            base_url=options['BASE_URL'],
            auth=auth,
            verify=options['VERIFY']
        )

    config.pluginmanager.register(plugin, XRAY_PLUGIN)
    config.addinivalue_line(
        'markers', 'xray(JIRA_ID): mark test with JIRA XRAY test case ID'
    )


def pytest_collection_modifyitems(config: Config, items: List[Item]) -> None:
    if not config.getoption(JIRA_XRAY_FLAG):
        return

    for item in items:
        associate_marker_metadata_for(item)


def pytest_terminal_summary(terminalreporter: TerminalReporter, exitstatus: ExitCode, config: Config) -> None:
    if not config.getoption(JIRA_XRAY_FLAG):
        return

    test_execution_id = terminalreporter.config.getoption(XRAY_EXECUTION_ID)
    test_plan_id = terminalreporter.config.getoption(XRAY_TEST_PLAN_ID)
    is_cloud_server = terminalreporter.config.getoption(JIRA_CLOUD)

    if is_cloud_server:
        status_builder = StatusBuilder(CloudStatus)
    else:
        status_builder = StatusBuilder(Status)

    test_execution = TestExecution(
        test_execution_key=test_execution_id,
        test_plan_key=test_plan_id
    )

    stats = terminalreporter.stats
    if 'passed' in stats:
        for item in stats['passed']:
            test_key = get_test_key_for(item)
            if test_key:
                tc = TestCase(test_key, status_builder('PASS'))
                test_execution.append(tc)
    if 'failed' in stats:
        for item in stats['failed']:
            test_key = get_test_key_for(item)
            if test_key:
                tc = TestCase(test_key, status_builder('FAIL'), item.longreprtext)
                test_execution.append(tc)
    if 'skipped' in stats:
        for item in stats['skipped']:
            test_key = get_test_key_for(item)
            if test_key:
                tc = TestCase(test_key, status_builder('ABORTED'), item.longreprtext)
                test_execution.append(tc)

    publisher = terminalreporter.config.pluginmanager.get_plugin(XRAY_PLUGIN)
    try:
        issue_id = publisher.publish(test_execution.as_dict())
    except XrayError as exc:
        terminalreporter.ensure_newline()
        terminalreporter.section('Jira XRAY', sep='-', red=True, bold=True)
        terminalreporter.write_line('Could not publish results to Jira XRAY!')
        if exc.message:
            terminalreporter.write_line(exc.message)
    else:
        if issue_id and terminalreporter.config.getoption(XRAYPATH):
            terminalreporter.write_sep(
                '-', f'Generated XRAY execution report file: {Path(issue_id).absolute()}'
            )
        elif issue_id:
            terminalreporter.write_sep(
                '-', f'Uploaded results to JIRA XRAY. Test Execution Id: {issue_id}'
            )
