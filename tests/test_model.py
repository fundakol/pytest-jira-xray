import os
from unittest import mock

import pytest

from pytest_xray import constant
from pytest_xray.helper import TestExecution


def test_testcase_output_dictionary(testcase):
    assert testcase.as_dict() == {
        'testKey': 'JIRA-1',
        'comment': '{noformat:borderWidth=0px|bgColor=transparent}Test{noformat}',
        'status': 'PASS',
    }


@pytest.mark.usefixtures('mock_datetime')
def test_test_execution_output_dictionary(testcase):
    te = TestExecution()
    te.tests = [testcase]
    assert te.as_dict() == {
        'info': {
            'finishDate': '2021-04-23T16:30:02+0000',
            'startDate': '2021-04-23T16:30:02+0000',
            'summary': 'Execution of automated tests',
        },
        'tests': [
            {
                'comment': '{noformat:borderWidth=0px|bgColor=transparent}Test{noformat}',
                'status': 'PASS',
                'testKey': 'JIRA-1',
            }
        ],
    }


@pytest.mark.usefixtures('mock_datetime')
def test_test_execution_output_dictionary_with_test_plan_id(testcase):
    te = TestExecution(test_plan_key='Jira-10')
    te.tests = [testcase]
    assert te.as_dict() == {
        'info': {
            'finishDate': '2021-04-23T16:30:02+0000',
            'startDate': '2021-04-23T16:30:02+0000',
            'testPlanKey': 'Jira-10',
            'summary': 'Execution of automated tests',
        },
        'tests': [
            {
                'comment': '{noformat:borderWidth=0px|bgColor=transparent}Test{noformat}',
                'status': 'PASS',
                'testKey': 'JIRA-1',
            }
        ],
    }


@pytest.mark.usefixtures('mock_datetime')
def test_test_execution_output_dictionary_with_test_execution_id(testcase):
    te = TestExecution(test_plan_key='Jira-10', test_execution_key='JIRA-20')
    te.tests = [testcase]
    assert te.as_dict() == {
        'testExecutionKey': 'JIRA-20',
        'info': {
            'finishDate': '2021-04-23T16:30:02+0000',
            'startDate': '2021-04-23T16:30:02+0000',
            'testPlanKey': 'Jira-10',
        },
        'tests': [
            {
                'comment': '{noformat:borderWidth=0px|bgColor=transparent}Test{noformat}',
                'status': 'PASS',
                'testKey': 'JIRA-1',
            }
        ],
    }


@pytest.mark.usefixtures('mock_datetime')
def test_test_execution_full_model(testcase):
    te = TestExecution(
        test_plan_key='Jira-10',
        test_execution_key='JIRA-20',
        test_environments=['My local laptop'],
        fix_version='1.0',
        summary='My Test Suite',
        description='Im doing stuff',
    )
    te.tests = [testcase]
    assert te.as_dict() == {
        'testExecutionKey': 'JIRA-20',
        'info': {
            'finishDate': '2021-04-23T16:30:02+0000',
            'startDate': '2021-04-23T16:30:02+0000',
            'testPlanKey': 'Jira-10',
            'version': '1.0',
            'testEnvironments': ['My local laptop'],
            'summary': 'My Test Suite',
            'description': 'Im doing stuff',
        },
        'tests': [
            {
                'comment': '{noformat:borderWidth=0px|bgColor=transparent}Test{noformat}',
                'status': 'PASS',
                'testKey': 'JIRA-1',
            }
        ],
    }


@pytest.mark.usefixtures('mock_datetime')
@mock.patch.dict(
    os.environ,
    {
        constant.ENV_TEST_EXECUTION_FIX_VERSION: '1.1',
        constant.ENV_TEST_EXECUTION_TEST_ENVIRONMENTS: 'MyLocalLaptop And TheLiveSystem',
    },
)
def test_test_execution_environ_model(testcase):
    te = TestExecution(
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
            ],
        },
        'tests': [
            {
                'comment': '{noformat:borderWidth=0px|bgColor=transparent}Test{noformat}',
                'status': 'PASS',
                'testKey': 'JIRA-1',
            }
        ],
    }
