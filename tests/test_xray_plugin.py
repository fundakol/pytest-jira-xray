import json
import textwrap
from pathlib import Path

import pytest

RESOURCE_DIR: Path = Path(__file__).parent.joinpath('resources')


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


@pytest.fixture()
def xray_tests_multi(testdir):
    test_example = textwrap.dedent(
        """\
        import pytest

        @pytest.mark.xray(['JIRA-1', 'JIRA-2'])
        def test_pass():
            assert True
        """)  # noqa: W293,W291
    testdir.makepyfile(test_example)
    return testdir


@pytest.fixture()
def xray_tests_multi_fail(testdir):
    test_example = textwrap.dedent(
        """\
        import pytest

        @pytest.mark.xray(['JIRA-1', 'JIRA-2'])
        def test_fail():
            assert 0 == 1
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
        '*--api-key-auth*Use API Key authentication*',
        '*--token-auth*Use token authentication*',
        '*--client-secret-auth*Use client secret authentication*',
        '*--execution=ExecutionId*', '*XRAY Test Execution ID*',
        '*--testplan=TestplanId*', '*XRAY Test Plan ID*',
        '*--xraypath=path*Do not upload to a server but create JSON report file at*', '*given path*',
    ])


@pytest.mark.parametrize(
    'cli_options',
    [
        ('--jira-xray',),
        ('--jira-xray', '--cloud', '--client-secret-auth'),
        ('--jira-xray', '--cloud', '--token-auth'),
        ('--jira-xray', '--cloud', '--api-key-auth')
    ],
    ids=['DC Server', 'Cloud client secret', 'Could token', 'Could api key']
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


def test_if_user_can_modify_results_with_hooks(xray_tests):
    xray_file = xray_tests.tmpdir.join('xray.json')
    xray_tests.makeconftest("""
        def pytest_xray_results(results):
            results['info']['user'] = 'Test User'
    """)
    result = xray_tests.runpytest('--jira-xray', '--xraypath', str(xray_file))
    assert result.ret == 0
    xray_result = json.load(xray_file.open())
    assert 'user' in xray_result['info']
    assert xray_result['info']['user'] == 'Test User'


def test_if_user_can_attache_evidences(xray_tests):
    expected_tests = [
        {'comment': '',
         'evidences': [
             {
                 'ContentType': 'plain/text',
                 'data': 'ZXZpZGVuY2U=',
                 'filename': 'test.log'
             },
             {
                 'ContentType': 'image/png',
                 'data': 'iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAH'
                         '0lEQVQIW2OcNm3afwY0wEi+ID8/PwOKdpCAjIwMAwBGOw558x9CSQAAAABJRU5ErkJggg==',
                 'filename': 'screenshot.png'
             },
             {
                 'ContentType': 'image/jpeg',
                 'data': '/9j/4AAQSkZJRgABAQAAAQABAAD/4QBiRXhpZgAATU0AKgAAAAgABQESAAMAAAABAAEAAAEa'
                         'AAUAAAABAAAASgEbAAUAAAABAAAAUgEoAAMAAAABAAEAAAITAAMAAAABAAEAAAAAAAAAAAABA'
                         'AAAAQAAAAEAAAAB/9sAQwADAgICAgIDAgICAwMDAwQGBAQEBAQIBgYFBgkICgoJCAkJCgwPDAo'
                         'LDgsJCQ0RDQ4PEBAREAoMEhMSEBMPEBAQ/8AACwgABQAFAQERAP/EABQAAQAAAAAAAAAAAAAAAA'
                         'AAAAf/xAAcEAACAgIDAAAAAAAAAAAAAAABAgMGBBEAE2H/2gAIAQEAAD8AXKtVorDFkSSZjw9LKoCoDvYPvP/Z',
                 'filename': 'screenshot.jpeg'
             }
         ],
         'status': 'PASS',
         'testKey': 'JIRA-1'}
    ]

    xray_file = xray_tests.tmpdir.join('xray.json')
    xray_tests.makeconftest(f"""
        import pytest
        from pytest_xray import evidence

        @pytest.hookimpl(hookwrapper=True)
        def pytest_runtest_makereport(item, call):
            outcome = yield
            report = outcome.get_result()
            evidences = getattr(report, "evidences", [])
            if report.when == "call":
                evidences.append(
                    evidence.text(data='evidence', filename="test.log")
                )
                evidences.append(
                    evidence.png(
                        data=open('{RESOURCE_DIR}/screenshot.png', 'rb').read(),
                        filename='screenshot.png'
                    )
                )
                evidences.append(
                    evidence.jpeg(
                        data=open('{RESOURCE_DIR}/screenshot.jpeg', 'rb').read(),
                        filename='screenshot.jpeg'
                    )
                )
                report.evidences = evidences
    """)
    result = xray_tests.runpytest('--jira-xray', '--xraypath', str(xray_file))
    assert result.ret == 0
    xray_result = json.load(xray_file.open())
    assert 'tests' in xray_result
    assert xray_result['tests'] == expected_tests


def test_jira_xray_plugin_multiple_ids(xray_tests_multi):
    xray_file = xray_tests_multi.tmpdir.join('xray.json')
    result = xray_tests_multi.runpytest('--jira-xray', '--xraypath', str(xray_file))
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines([
        '*Generated XRAY execution report file:*xray.json*',
    ])
    assert result.ret == 0
    assert not result.errlines
    assert xray_file.exists()
    with open(xray_file) as f:
        data = json.load(f)

    assert len(data['tests']) == 2
    assert data['tests'][0]['testKey'] == 'JIRA-1'
    assert data['tests'][1]['testKey'] == 'JIRA-2'


def test_jira_xray_plugin_multiple_ids_fail(xray_tests_multi_fail):
    xray_file = xray_tests_multi_fail.tmpdir.join('xray.json')
    result = xray_tests_multi_fail.runpytest(
        '--jira-xray',
        '--xraypath',
        str(xray_file)
    )
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines([
        '*Generated XRAY execution report file:*xray.json*',
    ])
    assert result.ret == 1
    assert xray_file.exists()
    with open(xray_file) as f:
        data = json.load(f)

    assert len(data['tests']) == 2
    print(data['tests'])


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


def test_duplicated_ids(testdir):
    testdir.makepyfile(textwrap.dedent(
        """\
        import pytest

        @pytest.mark.xray('JIRA-1')
        def test_pass():
            assert True

        @pytest.mark.xray('JIRA-1')
        def test_pass_2():
            assert False
        """)
    )

    report_file = testdir.tmpdir / 'xray.json'

    result = testdir.runpytest(
        '--jira-xray',
        f'--xraypath={report_file}',
        '-v',
    )

    assert result.ret == 3
    assert 'Duplicated test case ids' in str(result.stdout)

    result = testdir.runpytest(
        '--jira-xray',
        '--allow-duplicate-ids',
        f'--xraypath={report_file}',
        '-v',
    )

    assert result.ret == 1
    assert 'Duplicated test case ids' not in str(result.stdout)

    result.assert_outcomes(passed=1, failed=1)
    assert report_file.exists()
    with open(report_file) as file:
        data = json.load(file)

    xray_statuses = set((t['testKey'], t['status']) for t in data['tests'])
    assert xray_statuses == {
        ('JIRA-1', 'FAIL'),
    }
