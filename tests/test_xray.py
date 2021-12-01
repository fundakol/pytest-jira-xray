import json
import textwrap

import pytest


@pytest.fixture()
def xray_tests(testdir):
    test_example = textwrap.dedent(
        """\
        import pytest 
        
        @pytest.mark.xray('JIRA-1')
        def test_pass():
            assert True
        """)  # noqa: W293,W291
    testdir.makepyfile(test_example)
    return testdir


def test_help_message(xray_tests):
    result = xray_tests.runpytest(
        '--help',
    )
    result.stdout.fnmatch_lines([
        'Jira Xray report:',
        '*--jira-xray*Upload test results to JIRA XRAY*',
        '*--cloud*Use with JIRA XRAY could server*',
        '*--execution=ExecutionId*', '*XRAY Test Execution ID*',
        '*--testplan=TestplanId*', '*XRAY Test Plan ID*',
        '*--xraypath=path*Do not upload to a server but create JSON report file at*', '*given path*',
    ])


@pytest.mark.parametrize(
    'cli_options',
    [
        ('--jira-xray',),
        ('--jira-xray', '--cloud')
    ],
    ids=['DC Server', 'Cloud']
)
def test_jira_xray_plugin(xray_tests, cli_options):
    result = xray_tests.runpytest(*cli_options)
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines([
        '*Uploaded results to JIRA XRAY. Test Execution Id: 1000*',
    ])
    assert result.ret == 0
    assert not result.errlines


def test_jira_xray_plugin_exports_to_file(xray_tests):
    xray_file = xray_tests.tmpdir.join('xray.json')
    result = xray_tests.runpytest('--jira-xray', '--xraypath', str(xray_file))
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines([
        '*Generated XRAY execution report file:*xray.json*',
    ])
    assert result.ret == 0
    assert not result.errlines
    assert xray_file.exists()


def test_xray_with_all_test_types(testdir):
    testdir.makepyfile(textwrap.dedent(
        """\
        import pytest

        @pytest.fixture
        def error_fixture():
            assert 0

        @pytest.mark.xray('JIRA-1')
        def test_ok():
            print("ok")

        @pytest.mark.xray('JIRA-2')
        def test_fail():
            assert 0

        @pytest.mark.xray('JIRA-3')
        def test_error(error_fixture):
            pass

        @pytest.mark.xray('JIRA-4')
        def test_skip():
            pytest.skip("skipping this test")

        @pytest.mark.xray('JIRA-5')
        def test_xfail():
            pytest.xfail("xfailing this test")

        @pytest.mark.xfail(reason="always xfail")
        @pytest.mark.xray('JIRA-6')
        def test_xpass():
            pass
        """))
    report_file = testdir.tmpdir / 'xray.json'

    result = testdir.runpytest(
        '--jira-xray',
        f'--xraypath={report_file}',
        '-v',
    )

    assert result.ret == 1
    result.assert_outcomes(errors=1, failed=1, passed=1, skipped=1, xfailed=1, xpassed=1)
    assert report_file.exists()
    with open(report_file) as file:
        data = json.load(file)

    xray_statuses = set((t['testKey'], t['status']) for t in data['tests'])
    assert xray_statuses == {
        ('JIRA-1', 'PASS'),
        ('JIRA-2', 'FAIL'),
        ('JIRA-3', 'FAIL'),
        ('JIRA-4', 'ABORTED'),
        ('JIRA-5', 'FAIL'),
        ('JIRA-6', 'PASS')
    }


def test_if_tests_without_xray_id_are_not_included(testdir):
    testdir.makepyfile(textwrap.dedent(
        """\
        import pytest

        @pytest.mark.xray('JIRA-1')
        def test_pass():
            assert True

        def test_pass_without_id():
            assert True
        """)
    )

    report_file = testdir.tmpdir / 'xray.json'

    result = testdir.runpytest(
        '--jira-xray',
        f'--xraypath={report_file}',
        '-v',
    )

    assert result.ret == 0
    result.assert_outcomes(passed=2)
    assert report_file.exists()
    with open(report_file) as file:
        data = json.load(file)

    xray_statuses = set((t['testKey'], t['status']) for t in data['tests'])
    assert xray_statuses == {
        ('JIRA-1', 'PASS'),
    }
