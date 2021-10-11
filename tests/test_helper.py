from pytest_xray.helper import StatusBuilder, Status, CloudStatus
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
