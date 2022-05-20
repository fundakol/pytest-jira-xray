import pytest

from pytest_xray.helper import (
    Status,
    TestCase as _TestCase,  # to avoid warnings from pytest
    TestExecution as _TestExecution,
    STATUS_STR_MAPPER_CLOUD
)


@pytest.mark.parametrize(
    'status, expected_status',
    [
        (Status.PASS, 'PASS'),
        (Status.FAIL, 'FAIL'),
        (Status.ABORTED, 'ABORTED')
    ]
)
def test_testcase_returns_correct_status(status, expected_status):
    test = _TestCase(
        'JIRA-1',
        status,
        'hello'
    )
    assert str(test.as_dict()['status']) == expected_status


@pytest.mark.parametrize(
    'status, expected_status',
    [
        (Status.PASS, 'PASSED'),
        (Status.FAIL, 'FAILED'),
        (Status.ABORTED, 'ABORTED')
    ]
)
def test_status_builder_for_cloud_server_returns_correct_status(status, expected_status):
    test = _TestCase(
        'JIRA-1',
        status,
        'hello',
        status_str_mapper=STATUS_STR_MAPPER_CLOUD,
    )
    assert str(test.as_dict()['status']) == expected_status


def test_merge_test_cases():
    t1 = _TestCase(
        'JIRA-1',
        Status.PASS,
        'hello'
    )

    t2 = _TestCase(
        'JIRA-1',
        Status.FAIL,
        'hi'
    )

    t3 = _TestCase(
        'JIRA-2',
        Status.FAIL,
        'hi'
    )

    t1.merge(t2)

    assert t1.test_key == 'JIRA-1'
    assert t1.status == Status.FAIL
    assert t1.comment == 'hello\n' + '-' * 80 + '\nhi'

    with pytest.raises(ValueError):
        t1.merge(t3)


def test_find_test_case():
    execution = _TestExecution()
    execution.append(
        _TestCase(
            'JIRA-1',
            Status.PASS,
            ''
        )
    )

    execution.append(
        _TestCase(
            'JIRA-2',
            Status.FAIL,
            'hi'
        )
    )

    res = execution.find_test_case('JIRA-2')

    assert res.test_key == 'JIRA-2'
    assert res.status == Status.FAIL

    with pytest.raises(KeyError):
        execution.find_test_case('JIRA-42')
