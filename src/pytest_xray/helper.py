import datetime as dt
import enum
import os
from os import environ
from typing import List, Dict, Union, Any, Type, Optional

from pytest_xray.constant import DATETIME_FORMAT
from pytest_xray.exceptions import XrayError


class Status(str, enum.Enum):
    """Mapping status to string accepted by Jira DC server."""
    TODO = 'TODO'
    EXECUTING = 'EXECUTING'
    PENDING = 'PENDING'
    PASS = 'PASS'
    FAIL = 'FAIL'
    ABORTED = 'ABORTED'
    BLOCKED = 'BLOCKED'


class CloudStatus(str, enum.Enum):
    """Mapping status to string accepted by Jira cloud."""
    TODO = 'TODO'
    EXECUTING = 'EXECUTING'
    PENDING = 'PENDING'
    PASS = 'PASSED'
    FAIL = 'FAILED'
    ABORTED = 'ABORTED'
    BLOCKED = 'BLOCKED'


class StatusBuilder:
    """Class helps to get proper status for Jira Server/DC."""

    def __init__(self, status_enum: Type[enum.Enum]):
        self.status = status_enum

    def __call__(self, status: str) -> enum.Enum:
        return self.status(getattr(self.status, status)).value


class TestCase:

    def __init__(
            self,
            test_key: str,
            status: Union[enum.Enum, str],
            comment: Optional[str] = None,
    ):
        self.test_key = test_key
        self.status = status
        self.comment = comment or ''

    def as_dict(self) -> Dict[str, str]:
        return dict(
            testKey=self.test_key,
            status=str(self.status),
            comment=self.comment,
        )


class TestExecution:

    def __init__(
            self,
            test_execution_key: str = None,
            test_plan_key: str = None,
            user: str = None,
            revision: str = None,
            tests: List = None
    ):
        self.test_execution_key = test_execution_key
        self.test_plan_key = test_plan_key or ''
        self.user = user or ''
        self.revision = revision or ''
        self.start_date = dt.datetime.now(tz=dt.timezone.utc)
        self.finish_date = None
        self.tests = tests or []

    def append(self, test: Union[dict, TestCase]) -> None:
        if not isinstance(test, TestCase):
            test = TestCase(**test)
        self.tests.append(test)

    def as_dict(self) -> Dict[str, Any]:
        if self.finish_date is None:
            self.finish_date = dt.datetime.now(tz=dt.timezone.utc)

        tests = [test.as_dict() for test in self.tests]
        info = dict(
            startDate=self.start_date.strftime(DATETIME_FORMAT),
            finishDate=self.finish_date.strftime(DATETIME_FORMAT)
        )
        data = dict(
            info=info,
            tests=tests
        )
        if self.test_plan_key:
            info['testPlanKey'] = self.test_plan_key
        if self.test_execution_key:
            data['testExecutionKey'] = self.test_execution_key
        return data


def get_base_options() -> dict:
    options = {}
    try:
        base_url = environ['XRAY_API_BASE_URL']
    except KeyError as e:
        raise XrayError(
            'pytest-jira-xray plugin requires environment variable: XRAY_API_BASE_URL'
        ) from e

    verify = os.environ.get('XRAY_API_VERIFY_SSL', 'True')

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


def get_basic_auth() -> dict:
    options = get_base_options()
    try:
        user = environ['XRAY_API_USER']
        password = environ['XRAY_API_PASSWORD']
    except KeyError as e:
        raise XrayError(
            'Basic authentication requires environment variables: '
            'XRAY_API_USER, XRAY_API_PASSWORD'
        ) from e

    options['USER'] = user
    options['PASSWORD'] = password
    return options


def get_bearer_auth() -> dict:
    options = get_base_options()
    try:
        client_id = environ['XRAY_CLIENT_ID']
        client_secret = environ['XRAY_CLIENT_SECRET']
    except KeyError as e:
        raise XrayError(
            'Bearer authentication requires environment variables: '
            'XRAY_CLIENT_ID, XRAY_CLIENT_SECRET'
        ) from e

    options['CLIENT_ID'] = client_id
    options['CLIENT_SECRET'] = client_secret
    return options
