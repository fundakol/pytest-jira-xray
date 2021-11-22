import textwrap

import pytest


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
        """)  # noqa: W293,W291
    testdir.makepyfile(test_example)


@pytest.mark.parametrize(
    'cli_options',
    [
        ('--jira-xray',),
        ('--jira-xray', '--cloud')
    ],
    ids=['DC Server', 'Cloud']
)
def test_jira_xray_plugin(testdir, cli_options):
    result = testdir.runpytest(*cli_options)
    result.assert_outcomes(passed=1, failed=1, skipped=1)
    result.stdout.fnmatch_lines([
        '*Uploaded results to JIRA XRAY. Test Execution Id: 1000*',
    ])
    assert result.ret == 1
    assert not result.errlines


def test_jira_xray_plugin_exports_to_file(testdir, tmpdir):
    xray_file = tmpdir.join('xray.json')
    result = testdir.runpytest('--jira-xray', '--xraypath', str(xray_file))
    result.assert_outcomes(passed=1, failed=1, skipped=1)
    result.stdout.fnmatch_lines([
        '*Generated XRAY execution report file:*xray.json*',
    ])
    assert result.ret == 1
    assert not result.errlines
