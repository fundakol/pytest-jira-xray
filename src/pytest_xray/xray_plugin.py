import datetime as dt
import os
from pathlib import Path
from typing import List, Optional

import pytest
from _pytest.config import Config, ExitCode
from _pytest.mark import Mark
from _pytest.nodes import Item
from _pytest.reports import TestReport
from _pytest.terminal import TerminalReporter

from pytest_xray.constant import (
    JIRA_CLOUD,
    XRAY_ALLOW_DUPLICATE_IDS,
    XRAY_EXECUTION_ID,
    XRAY_MARKER_NAME,
    XRAY_TEST_PLAN_ID,
    XRAYPATH,
)
from pytest_xray.exceptions import XrayError
from pytest_xray.helper import (
    STATUS_STR_MAPPER_CLOUD,
    STATUS_STR_MAPPER_JIRA,
    Status,
    TestCase,
    TestExecution,
)


class XrayPlugin:

    def __init__(self, config, publisher):
        self.config = config
        self.publisher = publisher
        self.test_execution_id: str = self.config.getoption(XRAY_EXECUTION_ID)
        self.test_plan_id: str = self.config.getoption(XRAY_TEST_PLAN_ID)
        self.is_cloud_server: str = self.config.getoption(JIRA_CLOUD)
        self.allow_duplicate_ids: bool = self.config.getoption(XRAY_ALLOW_DUPLICATE_IDS)
        logfile = self.config.getoption(XRAYPATH)
        self.logfile: Optional[str] = self._get_normalize_logfile(logfile) if logfile else None
        self.issue_id = None  # issue id returned by XRAY sersver
        self.exception = None  # keeps an exception if raised by XrayPlublisher
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

    def _get_test_keys(self, item: Item) -> List[str]:
        """Return JIRA ids associated with test item"""
        marker = self._get_xray_marker(item)
        if not marker:
            return []

        test_keys: List[str]
        if isinstance(marker.args[0], str):
            test_keys = [marker.args[0]]
        elif isinstance(marker.args[0], list):
            test_keys = list(marker.args[0])
        else:
            raise XrayError('xray marker can only accept strings or lists')
        return test_keys

    def _verify_jira_ids_for_items(self, items: List[Item]) -> None:
        """Verify duplicated jira ids."""
        jira_ids: List[str] = []
        duplicated_jira_ids: List[str] = []

        for item in items:
            test_keys = self._get_test_keys(item)
            if not test_keys:
                continue

            for test_key in test_keys:
                if test_key in jira_ids:
                    duplicated_jira_ids.append(test_key)
                else:
                    jira_ids.append(test_key)

            if duplicated_jira_ids and not self.allow_duplicate_ids:
                raise XrayError(f'Duplicated test case ids: {duplicated_jira_ids}')

    @staticmethod
    def _get_xray_marker(item: Item) -> Optional[Mark]:
        return item.get_closest_marker(XRAY_MARKER_NAME)

    def pytest_sessionstart(self, session):
        self.test_execution.start_date = dt.datetime.now(tz=dt.timezone.utc)

    @pytest.hookimpl(tryfirst=True, hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()
        if not hasattr(report, 'test_keys'):
            report.test_keys = {}
        test_keys = self._get_test_keys(item)
        if test_keys and item.nodeid not in report.test_keys:
            report.test_keys[item.nodeid] = test_keys

    def pytest_runtest_logreport(self, report: TestReport):
        status = self._get_status_from_report(report)
        if status is None:
            return

        test_keys = report.test_keys.get(report.nodeid)
        if test_keys is None:
            return

        evidences = getattr(report, 'evidences', [])
        for test_key in test_keys:
            new_test_case = TestCase(
                test_key=test_key,
                status=status,
                comment=report.longreprtext,
                status_str_mapper=self.status_str_mapper,
                evidences=evidences
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
        self._verify_jira_ids_for_items(items)

    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        self.test_execution.finish_date = dt.datetime.now(tz=dt.timezone.utc)
        results = self.test_execution.as_dict()
        session.config.pluginmanager.hook.pytest_xray_results(
            results=results, session=session
        )
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
