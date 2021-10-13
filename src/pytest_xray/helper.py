import datetime as dt
import enum
import os
from os import environ
from typing import List, Dict, Union, Any, Type, Optional

from _pytest.mark import Mark
from _pytest.nodes import Item

from pytest_xray.constant import XRAY_MARKER_NAME, DATETIME_FORMAT
from pytest_xray.exceptions import XrayError

_test_keys = {}


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
            comment: str = None,
            duration: float = 0.0
    ):
        self.test_key = test_key
        self.status = status
        self.comment = comment or ''
        self.duration = duration

    def as_dict(self) -> Dict[str, str]:
        return dict(testKey=self.test_key,
                    status=str(self.status),
                    comment=self.comment)


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
        self.tests = tests or []

    def append(self, test: Union[dict, TestCase]) -> None:
        if not isinstance(test, TestCase):
            test = TestCase(**test)
        self.tests.append(test)

    def as_dict(self) -> Dict[str, Any]:
        tests = [test.as_dict() for test in self.tests]
        info = dict(startDate=self.start_date.strftime(DATETIME_FORMAT),
                    finishDate=dt.datetime.now(tz=dt.timezone.utc).strftime(DATETIME_FORMAT))
        data = dict(info=info,
                    tests=tests)
        if self.test_plan_key:
            info['testPlanKey'] = self.test_plan_key
        if self.test_execution_key:
            data['testExecutionKey'] = self.test_execution_key
        return data


def _get_xray_marker(item: Item) -> Optional[Mark]:
    return item.get_closest_marker(XRAY_MARKER_NAME)


def associate_marker_metadata_for(item: Item) -> None:
    """Store XRAY test id for test item."""
    marker = _get_xray_marker(item)
    if not marker:
        return

    test_key = marker.args[0]
    _test_keys[item.nodeid] = test_key


def get_test_key_for(item: Item) -> Optional[str]:
    """Return XRAY test id for item."""
    test_id = _test_keys.get(item.nodeid)
    if test_id:
        return test_id
    return None


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
        verify = True
    elif verify.upper() == 'FALSE':
        verify = False
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
