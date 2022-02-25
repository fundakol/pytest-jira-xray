from pytest_xray.helper import StatusBuilder, Status, CloudStatus, TestCase, \
    TestExecution
import pytest


@pytest.mark.parametrize(
    'status, expected_status',
    [
        ('PASS', 'PASS'),
        ('FAIL', 'FAIL'),
        ('ABORTED', 'ABORTED')
    ]
)
def test_status_builder_returns_correct_status(status, expected_status):
    status_builder = StatusBuilder(Status)
    assert str(status_builder(status)) == expected_status


@pytest.mark.parametrize(
    'status, expected_status',
    [
        ('PASS', 'PASSED'),
        ('FAIL', 'FAILED'),
        ('ABORTED', 'ABORTED')
    ]
)
def test_status_builder_for_cloud_server_returns_correct_status(status, expected_status):
    status_builder = StatusBuilder(CloudStatus)
    assert str(status_builder(status)) == expected_status


def test_merge_test_cases():
    t1 = TestCase(
        "JIRA-1",
        "PASS",
        "hello"
    )

    t2 = TestCase(
        "JIRA-1",
        "FAIL",
        "hi"
    )

    t3 = TestCase(
        "JIRA-2",
        "FAIL",
        "hi"
    )

    t1.merge(t2)

    assert t1.test_key == "JIRA-1"
    assert t1.status == "FAIL"
    assert t1.comment == "hello\n" + "-" * 80 + "\nhi"

    with pytest.raises(ValueError):
        t1.merge(t3)


def test_find_test_case():
    execution = TestExecution()
    execution.append(
        TestCase(
            "JIRA-1",
            "PASS",
            ""
        )
    )

    execution.append(
        TestCase(
            "JIRA-2",
            "FAIL",
            "hi"
        )
    )

    res = execution.find_test_case("JIRA-2")

    assert res.test_key == "JIRA-2"
    assert res.status == "FAIL"

    with pytest.raises(KeyError):
        execution.find_test_case("JIRA-42")


