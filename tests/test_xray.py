import re

pytest_plugins = 'pytester'


test_example_1 = """
import pytest 

@pytest.mark.xray('JIRA-1')
def test_pass():
    assert True, 'Not passed'

@pytest.mark.xray('JIRA-2')
def test_fail():
    assert False, 'Not passed'

@pytest.mark.skip('Skipped')
@pytest.mark.xray('JIRA-5')
def test_skip():
    assert True, 'Not passed'
"""


def test_jira_xray_plugin(testdir):
    testdir.makepyfile(test_example_1)
    result = testdir.runpytest('--jira-xray')
    result.assert_outcomes(passed=1, failed=1, skipped=1)
    assert len(result.errlines) == 0
    assert re.search('Uploaded results to JIRA XRAY', '\n'.join(result.outlines))
