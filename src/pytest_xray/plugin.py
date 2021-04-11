from os import environ
from typing import List

from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.nodes import Item
from _pytest.terminal import TerminalReporter

from pytest_xray.constant import JIRA_XRAY_FLAG, XRAY_PLUGIN, XRAY_TESTPLAN_ID, XRAY_EXECUTION_ID
from pytest_xray.helper import (associate_marker_metadata_for,
                                get_test_key_for,
                                Status,
                                TestCase,
                                TestExecution)
from pytest_xray.xray_publisher import XrayPublisher


def pytest_configure(config: Config) -> None:
    if not config.getoption(JIRA_XRAY_FLAG):
        return

    jira_url = environ["XRAY_API_BASE_URL"]
    auth = (environ["XRAY_API_USER"], environ["XRAY_API_PASSWORD"])

    plugin = XrayPublisher(base_url=jira_url, auth=auth)
    config.pluginmanager.register(plugin, XRAY_PLUGIN)

    config.addinivalue_line(
        "markers", "xray(JIRA_ID): mark test with JIRA XRAY test case ID"
    )


def pytest_addoption(parser: Parser):
    xray = parser.getgroup('Jira Xray report')
    xray.addoption(JIRA_XRAY_FLAG,
                   action="store_true",
                   default=False,
                   help="Upload test results to JIRA XRAY")
    xray.addoption(XRAY_EXECUTION_ID,
                   action="store",
                   default=None,
                   help="XRAY Test Execution ID")
    xray.addoption(XRAY_TESTPLAN_ID,
                   action="store",
                   default=None,
                   help="XRAY Test Plan ID")


def pytest_collection_modifyitems(config: Config, items: List[Item]) -> None:
    if not config.getoption(JIRA_XRAY_FLAG):
        return

    for item in items:
        associate_marker_metadata_for(item)


def pytest_terminal_summary(terminalreporter: TerminalReporter) -> None:
    if not terminalreporter.config.getoption(JIRA_XRAY_FLAG):
        return
    test_execution_id = terminalreporter.config.getoption(XRAY_EXECUTION_ID)
    test_plan_id = terminalreporter.config.getoption(XRAY_TESTPLAN_ID)

    test_execution = TestExecution(test_execution_key=test_execution_id,
                                   test_plan_key=test_plan_id)

    if "passed" in terminalreporter.stats:
        for each in terminalreporter.stats["passed"]:
            test_key = get_test_key_for(each)
            if test_key:
                tc = TestCase(test_key, Status.PASS)
                test_execution.append(tc)

    if "failed" in terminalreporter.stats:
        for each in terminalreporter.stats["failed"]:
            test_key = get_test_key_for(each)
            if test_key:
                tc = TestCase(test_key, Status.FAIL, each.longreprtext)
                test_execution.append(tc)
    if "skipped" in terminalreporter.stats:
        for each in terminalreporter.stats["skipped"]:
            test_key = get_test_key_for(each)
            if test_key:
                tc = TestCase(test_key, Status.ABORTED, each.longreprtext)
                test_execution.append(tc)

    publish_results = terminalreporter.config.pluginmanager.get_plugin(XRAY_PLUGIN)
    status = publish_results.publish(test_execution)
    if status:
        print('Test results published to JIRA-XRAY:', publish_results.base_url)
