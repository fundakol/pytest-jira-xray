import datetime as dt
import enum
import os
import re
from os import environ
from typing import Any, Dict, List, Optional, Union

from pytest_xray import constant
from pytest_xray.constant import (
    DATETIME_FORMAT,
    ENV_XRAY_API_BASE_URL,
    ENV_XRAY_API_KEY,
    ENV_XRAY_API_PASSWORD,
    ENV_XRAY_API_USER,
    ENV_XRAY_API_VERIFY_SSL,
    ENV_XRAY_CLIENT_ID,
    ENV_XRAY_CLIENT_SECRET,
)
from pytest_xray.exceptions import XrayError


class Status(str, enum.Enum):
    TODO = 'TODO'
    EXECUTING = 'EXECUTING'
    PENDING = 'PENDING'
    PASS = 'PASS'
    FAIL = 'FAIL'
    ABORTED = 'ABORTED'
    BLOCKED = 'BLOCKED'


# This is the hierarchy of the Status, from bottom to top.
# When merging two statuses, the highest will be picked.
# For example, a PASS and a FAIL will result in a FAIL,
# A TODO and an ABORTED in an ABORTED, A TODO and a PASS in a TODO.
STATUS_HIERARCHY = [
    Status.PASS,
    Status.TODO,
    Status.EXECUTING,
    Status.PENDING,
    Status.FAIL,
    Status.ABORTED,
    Status.BLOCKED,
]

# Maps the Status from the internal Status enum to the string representations
# requested by either the Cloud Jira, or the on-site Jira
STATUS_STR_MAPPER_CLOUD = {
    Status.TODO: 'TODO',
    Status.EXECUTING: 'EXECUTING',
    Status.PENDING: 'PENDING',
    Status.PASS: 'PASSED',
    Status.FAIL: 'FAILED',
    Status.ABORTED: 'ABORTED',
    Status.BLOCKED: 'BLOCKED',
}

# On-site jira uses the enum strings directly
STATUS_STR_MAPPER_JIRA = {x: x.value for x in Status}


class TestCase:
    def __init__(
        self,
        test_key: str,
        status: Status,
        comment: Optional[str] = None,
        status_str_mapper: Optional[Dict[Status, str]] = None,
        evidences: Optional[List[Dict[str, str]]] = None
    ):
        self.test_key = test_key
        self.status = status
        self.comment = comment or ''
        self.status_str_mapper = status_str_mapper or STATUS_STR_MAPPER_JIRA
        self.evidences = evidences or []

    def merge(self, other: 'TestCase'):
        """
        Merges this test case with other, in order to obtain
        a combined result. Comments will be just appended one after the other.
        status will be merged according to a priority list.
        Merge is only possible if the two tests have the same test_key
        """

        if self.test_key != other.test_key:
            raise ValueError(
                f'Cannot merge test with different test keys: '
                f'{self.test_key} {other.test_key}'
            )

        if self.comment == '':
            if other.comment != '':
                self.comment = other.comment
        else:
            if other.comment != '':
                self.comment += ('\n' + '-'*80 + '\n')
                self.comment += other.comment

        self.status = _merge_status(self.status, other.status)

    def as_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = dict(
            testKey=self.test_key,
            status=self.status_str_mapper[self.status],
            comment=self.comment,
        )
        if self.evidences:
            data['evidences'] = self.evidences
        return data


class TestExecution:

    def __init__(
        self,
        test_execution_key: Optional[str] = None,
        test_plan_key: Optional[str] = None,
        user: Optional[str] = None,
        revision: Optional[str] = None,
        tests: Optional[List[TestCase]] = None,
        test_environments: Optional[List[str]] = None,
        fix_version: Optional[str] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.test_execution_key = test_execution_key
        self.test_plan_key = test_plan_key or ''
        self.user = user or ''
        self.revision = revision or _from_environ_or_none(constant.ENV_TEST_EXECUTION_REVISION)
        self.start_date = dt.datetime.now(tz=dt.timezone.utc)
        self.finish_date = dt.datetime.now(tz=dt.timezone.utc)
        self.tests = tests or []
        self.test_environments = test_environments or _from_environ(
            constant.ENV_TEST_EXECUTION_TEST_ENVIRONMENTS,
            constant.ENV_MULTI_VALUE_SPLIT_PATTERN
        )
        self.fix_version = fix_version or _first_from_environ(constant.ENV_TEST_EXECUTION_FIX_VERSION)
        self.summary = summary or _from_environ_or_none(constant.ENV_TEST_EXECUTION_SUMMARY)
        self.description = description or _from_environ_or_none(constant.ENV_TEST_EXECUTION_DESC)

    def append(self, test: Union[dict, TestCase]) -> None:
        if not isinstance(test, TestCase):
            test = TestCase(**test)
        self.tests.append(test)

    def find_test_case(self, test_key: str) -> TestCase:
        """
        Searches a stored test case by identifier.
        If not found, raises KeyError
        """
        # Linear search, but who cares really of performance here?

        for test in self.tests:
            if test.test_key == test_key:
                return test

        raise KeyError(test_key)

    def as_dict(self) -> Dict[str, Any]:
        tests = [test.as_dict() for test in self.tests]
        info: Dict[str, Any] = dict(
            startDate=self.start_date.strftime(DATETIME_FORMAT),
            finishDate=self.finish_date.strftime(DATETIME_FORMAT),  # type: ignore
        )

        if self.fix_version:
            info['version'] = self.fix_version

        if self.test_environments and len(self.test_environments) > 0:
            info['testEnvironments'] = self.test_environments

        if self.summary:
            info['summary'] = self.summary

        if self.description:
            info['description'] = self.description

        if self.revision:
            info['revision'] = self.revision

        data: Dict[str, Any] = dict(
            info=info,
            tests=tests
        )
        if self.test_plan_key:
            info['testPlanKey'] = self.test_plan_key
        if self.test_execution_key:
            data['testExecutionKey'] = self.test_execution_key
        return data


def get_base_options() -> Dict[str, Any]:
    options = {}
    try:
        base_url = environ[ENV_XRAY_API_BASE_URL]
    except KeyError as e:
        raise XrayError(
            f'pytest-jira-xray plugin requires environment variable: {ENV_XRAY_API_BASE_URL}'
        ) from e

    verify = os.environ.get(ENV_XRAY_API_VERIFY_SSL, 'True')

    if verify.upper() == 'TRUE':
        verify = True  # type: ignore
    elif verify.upper() == 'FALSE':
        verify = False  # type: ignore
    else:
        if not os.path.exists(verify):
            raise XrayError(f'Cannot find certificate file "{verify}"')

    options['VERIFY'] = verify
    options['BASE_URL'] = base_url
    return options


def get_basic_auth() -> Dict[str, Any]:
    """Return basic authentication setup with username and password."""
    options = get_base_options()
    try:
        user = environ[ENV_XRAY_API_USER]
        password = environ[ENV_XRAY_API_PASSWORD]
    except KeyError as e:
        raise XrayError(
            'Basic authentication requires environment variables: '
            f'{ENV_XRAY_API_USER}, {ENV_XRAY_API_PASSWORD}'
        ) from e

    options['USER'] = user
    options['PASSWORD'] = password
    return options


def get_bearer_auth() -> Dict[str, Any]:
    """Return bearer authentication setup with Client ID and a Client Secret."""
    options = get_base_options()
    try:
        client_id = environ[ENV_XRAY_CLIENT_ID]
        client_secret = environ[ENV_XRAY_CLIENT_SECRET]
    except KeyError as e:
        raise XrayError(
            'Bearer authentication requires environment variables: '
            f'{ENV_XRAY_CLIENT_ID}, {ENV_XRAY_CLIENT_SECRET}'
        ) from e

    options['CLIENT_ID'] = client_id
    options['CLIENT_SECRET'] = client_secret
    return options


def get_api_key_auth() -> Dict[str, Any]:
    """Return personal access token authentication."""
    options = get_base_options()
    try:
        api_key = environ[ENV_XRAY_API_KEY]
    except KeyError as e:
        raise XrayError(
            f'API Key authentication requires environment variable: {ENV_XRAY_API_KEY}'
        ) from e

    options['API_KEY'] = api_key
    return options


def _from_environ_or_none(name: str) -> Optional[str]:
    if name in environ:
        val = environ[name].strip()
        if len(val) == 0:
            return None
    else:
        return None
    return val


def _first_from_environ(name: str, separator: Optional[str] = None) -> Optional[str]:
    return next(iter(_from_environ(name, separator)), None)


def _from_environ(name: str, separator: Optional[str] = None) -> List[str]:
    if name not in environ:
        return []

    param = environ[name]

    if separator:
        source = re.split(separator, param)
    else:
        source = [param]

    # Return stripped non empty values
    return list(filter(lambda x: len(x) > 0, map(lambda x: x.strip(), source)))


def _merge_status(status_1: Status, status_2: Status):
    """Merges the status of two tests."""

    return STATUS_HIERARCHY[max(
        STATUS_HIERARCHY.index(status_1),
        STATUS_HIERARCHY.index(status_2)
    )]
