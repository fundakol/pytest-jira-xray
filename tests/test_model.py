import datetime as dt
import os
from unittest import mock
from unittest.mock import patch

import pytest

from pytest_xray.helper import TestCase as _TestCase, TestExecution as _TestExecution
from pytest_xray import constant


def formatted_comment(comment: str):
    return f"{{noformat}}\n{comment}\n{{noformat}}"


@pytest.fixture
def date_time_now():
    return dt.datetime(2021, 4, 23, 16, 30, 2, 0, tzinfo=dt.timezone.utc)


@pytest.fixture
def testcase():
    return _TestCase(
        test_key='JIRA-1',
        comment='Test',
        status='PASS'
    )


@pytest.fixture
def testcase_with_steps_0():
    return _TestCase(
        test_key='JIRA-2',
        comment='Test2 - Step 1',
        status='PASS',
        test_step=0
    )


@pytest.fixture
def testcase_with_steps_1():
    return _TestCase(
        test_key='JIRA-2',
        comment='Test2 - Step 2',
        status='FAIL',
        test_step=1
    )


@pytest.fixture
def testcase_with_steps_2():
    return _TestCase(
        test_key='JIRA-2',
        comment='Test2 - Step 3',
        status='PASS',
        test_step=2
    )


def test_testcase_output_dictionary(testcase):
    assert testcase.as_dict() == {
        'testKey': 'JIRA-1',
        'comment': formatted_comment('Test'),
        'status': 'PASS',
        'steps': []
    }


def test_test_execution_output_dictionary(testcase, date_time_now):
    with patch('datetime.datetime') as dt_mock:
        dt_mock.now.return_value = date_time_now
        te = _TestExecution()
        te.tests = [testcase]
        assert te.as_dict() == {
            'info': {
                'finishDate': '2021-04-23T16:30:02+0000',
                'startDate': '2021-04-23T16:30:02+0000'
            },
            'tests': [
                {
                    'comment': formatted_comment('Test'),
                    'status': 'PASS',
                    'testKey': 'JIRA-1',
                    'steps': []
                }
            ]
        }


def test_test_execution_output_dictionary_with_test_plan_id(testcase, date_time_now):
    with patch('datetime.datetime') as dt_mock:
        dt_mock.now.return_value = date_time_now
        te = _TestExecution(test_plan_key='Jira-10')
        te.tests = [testcase]
        assert te.as_dict() == {
            'info': {
                'finishDate': '2021-04-23T16:30:02+0000',
                'startDate': '2021-04-23T16:30:02+0000',
                'testPlanKey': 'Jira-10'
            },
            'tests': [
                {
                    'comment': formatted_comment('Test'),
                    'status': 'PASS',
                    'testKey': 'JIRA-1',
                    'steps': []
                }
            ]
        }


def test_test_execution_output_dictionary_with_test_execution_id(testcase, date_time_now):
    with patch('datetime.datetime') as dt_mock:
        dt_mock.now.return_value = date_time_now
        te = _TestExecution(test_plan_key='Jira-10', test_execution_key='JIRA-20')
        te.tests = [testcase]
        assert te.as_dict() == {
            'testExecutionKey': 'JIRA-20',
            'info': {
                'finishDate': '2021-04-23T16:30:02+0000',
                'startDate': '2021-04-23T16:30:02+0000',
                'testPlanKey': 'Jira-10'
            },
            'tests': [
                {
                    'comment': formatted_comment('Test'),
                    'status': 'PASS',
                    'testKey': 'JIRA-1',
                    'steps': []
                }
            ]
        }


def test_test_execution_full_model(testcase, date_time_now):
    with patch('datetime.datetime') as dt_mock:
        dt_mock.now.return_value = date_time_now
        te = _TestExecution(
            test_plan_key='Jira-10',
            test_execution_key='JIRA-20',
            test_environments=['My local laptop'],
            fix_version='1.0',
            summary='My Test Suite',
            description='Im doing stuff'
        )
        te.tests = [testcase]
        assert te.as_dict() == {
            'testExecutionKey': 'JIRA-20',
            'info': {
                'finishDate': '2021-04-23T16:30:02+0000',
                'startDate': '2021-04-23T16:30:02+0000',
                'testPlanKey': 'Jira-10',
                'version': '1.0',
                'testEnvironments': [
                    'My local laptop'
                ],
                'summary': 'My Test Suite',
                'description': 'Im doing stuff'
            },
            'tests': [
                {
                    'comment': formatted_comment('Test'),
                    'status': 'PASS',
                    'testKey': 'JIRA-1',
                    'steps': []
                }
            ]
        }


@mock.patch.dict(os.environ, {
    constant.ENV_TEST_EXECUTION_FIX_VERSION: '1.1',
    constant.ENV_TEST_EXECUTION_TEST_ENVIRONMENTS: 'MyLocalLaptop And TheLiveSystem',
})
def test_test_execution_environ_model(testcase, date_time_now):
    with patch('datetime.datetime') as dt_mock:
        dt_mock.now.return_value = date_time_now
        te = _TestExecution(
            test_plan_key='Jira-10',
            test_execution_key='JIRA-20',
        )
        te.tests = [testcase]
        assert te.as_dict() == {
            'testExecutionKey': 'JIRA-20',
            'info': {
                'finishDate': '2021-04-23T16:30:02+0000',
                'startDate': '2021-04-23T16:30:02+0000',
                'testPlanKey': 'Jira-10',
                'version': '1.1',
                'testEnvironments': [
                    'MyLocalLaptop',
                    'And',
                    'TheLiveSystem',
                ]
            },
            'tests': [
                {
                    'comment': formatted_comment('Test'),
                    'status': 'PASS',
                    'testKey': 'JIRA-1',
                    'steps': []
                }
            ]
        }


def test_test_execution_with_step(testcase_with_steps_0, date_time_now):
    with patch('datetime.datetime') as dt_mock:
        dt_mock.now.return_value = date_time_now
        te = _TestExecution(
            test_plan_key='Jira-10',
            test_execution_key='JIRA-20',
            test_environments=['My local laptop'],
            fix_version='1.0',
            summary='My Test Suite',
            description='Im doing stuff'
        )
        te.tests = [testcase_with_steps_0]
        assert te.as_dict() == {
            'testExecutionKey': 'JIRA-20',
            'info': {
                'finishDate': '2021-04-23T16:30:02+0000',
                'startDate': '2021-04-23T16:30:02+0000',
                'testPlanKey': 'Jira-10',
                'version': '1.0',
                'testEnvironments': [
                    'My local laptop'
                ],
                'summary': 'My Test Suite',
                'description': 'Im doing stuff'
            },
            'tests': [
                {
                    'comment': '',
                    'status': 'PASS',
                    'testKey': 'JIRA-2',
                    'steps': [{'comment': formatted_comment('Test2 - Step 1'), 'status': 'PASS'}]
                }
            ]
        }


def test_test_execution_with_multiple_steps(
        testcase_with_steps_0,
        testcase_with_steps_1,
        testcase_with_steps_2,
        date_time_now):
    with patch('datetime.datetime') as dt_mock:
        dt_mock.now.return_value = date_time_now
        te = _TestExecution(
            test_plan_key='Jira-10',
            test_execution_key='JIRA-20',
            test_environments=['My local laptop'],
            fix_version='1.0',
            summary='My Test Suite',
            description='Im doing stuff'
        )
        testcase_with_steps_0.merge(testcase_with_steps_1)
        testcase_with_steps_0.merge(testcase_with_steps_2)
        te.tests = [testcase_with_steps_0]
        assert te.as_dict() == {
            'testExecutionKey': 'JIRA-20',
            'info': {
                'finishDate': '2021-04-23T16:30:02+0000',
                'startDate': '2021-04-23T16:30:02+0000',
                'testPlanKey': 'Jira-10',
                'version': '1.0',
                'testEnvironments': [
                    'My local laptop'
                ],
                'summary': 'My Test Suite',
                'description': 'Im doing stuff'
            },
            'tests': [
                {
                    'comment': '',
                    'status': 'FAIL',
                    'testKey': 'JIRA-2',
                    'steps': [
                        {'comment': formatted_comment('Test2 - Step 1'), 'status': 'PASS'},
                        {'comment': formatted_comment('Test2 - Step 2'), 'status': 'FAIL'},
                        {'comment': formatted_comment('Test2 - Step 3'), 'status': 'PASS'}
                        ]
                },
            ]
        }
