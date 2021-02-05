import datetime as dt
import enum
from typing import List, Dict, Union, Any

from pytest_xray.constant import XRAY_MARKER_NAME, DATETIME_FORMAT

_test_keys = {}


class Status(str, enum.Enum):
    TODO = 'TODO'
    EXECUTING = 'EXECUTING'
    PENDING = 'PENDING'
    PASS = 'PASS'
    FAIL = 'FAIL'
    ABORTED = 'ABORTED'
    BLOCKED = 'BLOCKED'


class TestCase:

    def __init__(self,
                 test_key: str,
                 status: str,
                 comment: str = None,
                 duration: float = 0.0):
        self.test_key = test_key
        self.status = Status(status)
        self.comment = comment or ''
        self.duration = duration

    def as_dict(self) -> Dict[str, str]:
        return dict(testKey=self.test_key,
                    status=self.status,
                    comment=self.comment)


class TestExecution:

    def __init__(self,
                 test_execution_key: str, *,
                 test_plan_key: str = None,
                 user: str = None,
                 revision: str = None,
                 tests: List = None):
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
        info = dict(startDate=self.start_date.strftime(DATETIME_FORMAT),
                    finishDate=dt.datetime.now(tz=dt.timezone.utc).strftime(DATETIME_FORMAT),
        )
        tests = [test.as_dict() for test in self.tests]
        return dict(testExecutionKey=self.test_execution_key,
                    info=info,
                    tests=tests)


def _get_xray_marker(item):
    return item.get_closest_marker(XRAY_MARKER_NAME)


def associate_marker_metadata_for(item):
    marker = _get_xray_marker(item)
    if not marker:
        return

    test_key = marker.args[0]
    _test_keys[item.nodeid] = test_key


def get_test_key_for(item):
    results = _test_keys.get(item.nodeid)
    if results:
        return results
    return None
