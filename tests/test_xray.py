import re
import textwrap

import pytest

pytest_plugins = ['pytester']


@pytest.fixture(autouse=True)
def xray_tests(testdir):
    test_example = textwrap.dedent(
        """\
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
        """)
    testdir.makepyfile(test_example)


@pytest.mark.parametrize(
    'cli_options',
    [
        ('--jira-xray',),
        ('--jira-xray', '--jira-cloud')
    ],
    ids=['DC Server', 'Cloud']
)
def test_jira_xray_plugin(testdir, cli_options):
    result = testdir.runpytest(*cli_options)
    result.assert_outcomes(passed=1, failed=1, skipped=1)
    assert len(result.errlines) == 0
    assert re.search('Uploaded results to JIRA XRAY', '\n'.join(result.outlines))
