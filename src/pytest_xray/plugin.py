from os import environ

from pytest_xray.constant import JIRA_XRAY_FLAG, XRAY_PLUGIN
from pytest_xray.helper import (associate_marker_metadata_for, get_test_key_for, Status, TestCase,
                                TestExecution)
from pytest_xray.xray_publisher import XrayPublisher


def pytest_configure(config):
    if not config.getoption(JIRA_XRAY_FLAG):
        return

    jira_url = str(environ["XRAY_API_BASE_URL"])
    auth = (str(environ["XRAY_API_USER"]), str(environ["XRAY_API_PASSWORD"]))

    plugin = XrayPublisher(base_url=jira_url, auth=auth)
    config.pluginmanager.register(plugin, XRAY_PLUGIN)

    config.addinivalue_line(
        "markers", "xray: mark test to run only on named environment"
    )


def pytest_addoption(parser):
    xray = parser.getgroup('Jira Xray report')
    xray.addoption(JIRA_XRAY_FLAG,
                   action="store",
                   default=None,
                   help="Upload test results to JIRA XRAY Test Execution")


def pytest_collection_modifyitems(config, items):
    if not config.getoption(JIRA_XRAY_FLAG):
        return

    for item in items:
        associate_marker_metadata_for(item)


def pytest_terminal_summary(terminalreporter):
    test_execution_id = terminalreporter.config.getoption(JIRA_XRAY_FLAG)
    if not test_execution_id:
        return

    test_execution = TestExecution(test_execution_id)

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
    publish_results.publish(test_execution)
