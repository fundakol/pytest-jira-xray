import json
import textwrap
from pathlib import Path
from unittest import mock

import pytest
import requests

RESOURCE_DIR: Path = Path(__file__).parent.joinpath('resources')


@pytest.fixture()
def xray_tests(testdir) -> pytest.Testdir:
    test_example = textwrap.dedent(
        """\
        import pytest

        @pytest.mark.xray('JIRA-1')
        def test_pass():
            assert True
        """
    )  # noqa: W293,W291
    testdir.makepyfile(test_example)
    return testdir


@pytest.fixture()
def xray_tests_multi(testdir) -> pytest.Testdir:
    test_example = textwrap.dedent(
        """\
        import pytest

        @pytest.mark.xray(['JIRA-1', 'JIRA-2'])
        def test_foo():
            assert True

        @pytest.mark.xray("JIRA-3", "JIRA-4")
        def test_bar():
            assert True
        """
    )  # noqa: W293,W291
    testdir.makepyfile(test_example)
    return testdir


@pytest.fixture()
def xray_tests_multi_fail(testdir) -> pytest.Testdir:
    test_example = textwrap.dedent(
        """\
        import pytest

        @pytest.mark.xray(['JIRA-1', 'JIRA-2'])
        def test_fail():
            assert 0 == 1
        """
    )  # noqa: W293,W291
    testdir.makepyfile(test_example)
    return testdir


def test_help_message(xray_tests):
    result = xray_tests.runpytest(
        '--help',
    )
    result.stdout.fnmatch_lines(
        [
            'Jira Xray report:',
            '*--jira-xray*Upload test results to JIRA XRAY*',
            '*--cloud*Use with JIRA XRAY cloud server*',
            '*--api-key-auth*Use Jira API Key authentication*',
            '*--client-secret-auth*Use client secret authentication*',
            '*--execution=ExecutionId*',
            '*XRAY Test Execution ID*',
            '*--testplan=TestplanId*',
            '*XRAY Test Plan ID*',
            '*--xraypath=path*Do not upload to a server but create JSON report file at*',
            '*given path*',
            '*--allow-duplicate-ids*',
            '*Allow test ids to be present on multiple pytest tests*',
            '*--add-captures*Add captures from log, stdout or/and stderr, to the*',
            '*report comment field*',
        ]
    )


@pytest.mark.parametrize(
    'cli_options',
    [
        ('--jira-xray',),
        ('--jira-xray', '--cloud', '--client-secret-auth'),
        ('--jira-xray', '--cloud', '--api-key-auth'),
    ],
    ids=['DC Server', 'Cloud client secret', 'Cloud api key'],
)
def test_jira_xray_plugin(fake_xray_server, xray_tests, cli_options):
    result = xray_tests.runpytest(*cli_options)
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            '*Uploaded results to JIRA XRAY. Test Execution Id: 1000*',
        ]
    )
    assert result.ret == 0
    assert not result.errlines


def test_jira_xray_plugin_exports_to_file(fake_xray_server, xray_tests):
    xray_file = xray_tests.tmpdir.join('xray.json')
    result = xray_tests.runpytest('--jira-xray', '--xraypath', str(xray_file))
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            '*Generated XRAY execution report file:*xray.json*',
        ]
    )
    assert result.ret == 0
    assert not result.errlines
    assert xray_file.exists()


def test_jira_xray_plugin_handles_http_error_504(xray_tests, pytester, httpserver, environment_variables):
    httpserver.expect_request('/rest/raven/2.0/import/execution').respond_with_data('Gateway Timeout', status=504)

    result = pytester.runpytest('--jira-xray')
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            '*Could not publish results to Jira XRAY!*',
            '*Could not post to JIRA service at*Response status code: 504*',
        ]
    )
    assert result.ret == 0
    assert not result.errlines


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


def test_if_user_can_attach_evidences(xray_tests):
    expected_tests = [
        {
            'comment': '{noformat:borderWidth=0px|bgColor=transparent}Test{noformat}',
            'evidences': [
                {'contentType': 'text/plain', 'data': 'ZXZpZGVuY2U=', 'filename': 'test.log'},
                {
                    'contentType': 'image/png',
                    'data': 'iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAH'
                    '0lEQVQIW2OcNm3afwY0wEi+ID8/PwOKdpCAjIwMAwBGOw558x9CSQAAAABJRU5ErkJggg==',
                    'filename': 'screenshot.png',
                },
                {
                    'contentType': 'image/jpeg',
                    'data': '/9j/4AAQSkZJRgABAQAAAQABAAD/4QBiRXhpZgAATU0AKgAAAAgABQESAAMAAAABAAEAAAEa'
                    'AAUAAAABAAAASgEbAAUAAAABAAAAUgEoAAMAAAABAAEAAAITAAMAAAABAAEAAAAAAAAAAAABA'
                    'AAAAQAAAAEAAAAB/9sAQwADAgICAgIDAgICAwMDAwQGBAQEBAQIBgYFBgkICgoJCAkJCgwPDAo'
                    'LDgsJCQ0RDQ4PEBAREAoMEhMSEBMPEBAQ/8AACwgABQAFAQERAP/EABQAAQAAAAAAAAAAAAAAAA'
                    'AAAAf/xAAcEAACAgIDAAAAAAAAAAAAAAABAgMGBBEAE2H/2gAIAQEAAD8AXKtVorDFkSSZjw9LKoCoDvYPvP/Z',
                    'filename': 'screenshot.jpeg',
                },
                {'contentType': 'text/html', 'data': 'PGgxPlRlc3Q8L2gxPg==', 'filename': 'test.html'},
                {'contentType': 'application/json', 'data': 'eyAidGVzdCIgOiAidGVzdCIgfQ==', 'filename': 'test.json'},
                {
                    'contentType': 'application/zip',
                    'data': 'UEsDBBQAAAAIAC6DvlYWgkkTUwAAAFgAAAAOABwAc2NyZWVuc2hvdC5wbmdVVAkAA1gHdmS4'
                    'B3ZkdXgLAAEE6AMAAAToAwAA6wzwc+flkuJiYGDg9fRwCQLSrCDMwQYke/PVngIpeU8XxxCO'
                    '6OQ5Zrm36tlMDnjsU7C3t2fuKpvQ0NPDw8zgZs1X+VneyROolMHT1c9lnVNCEwBQSwECHgMUA'
                    'AAACAAug75WFoJJE1MAAABYAAAADgAYAAAAAAAAAAAApIEAAAAAc2NyZWVuc2hvdC5wbmdVVA'
                    'UAA1gHdmR1eAsAAQToAwAABOgDAABQSwUGAAAAAAEAAQBUAAAAmwAAAAAA',
                    'filename': 'test.zip',
                },
            ],
            'status': 'PASS',
            'testKey': 'JIRA-1',
        }
    ]

    xray_file = xray_tests.tmpdir.join('xray.json')
    xray_tests.makeconftest(f"""
        import pytest
        from pytest_xray import evidence

        @pytest.hookimpl(hookwrapper=True)
        def pytest_runtest_makereport(item, call):
            outcome = yield
            report = outcome.get_result()
            report.longrepr = "Test"
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
                evidences.append(
                    evidence.html(data='<h1>Test</h1>', filename='test.html')
                )
                evidences.append(
                    evidence.json(
                        data='{{ "test" : "test" }}',
                        filename='test.json')
                )
                evidences.append(
                    evidence.zip(
                        data=open('{RESOURCE_DIR}/test.zip', 'rb').read(),
                        filename='test.zip')
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
    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(
        [
            '*Generated XRAY execution report file:*xray.json*',
        ]
    )
    assert result.ret == 0
    assert not result.errlines
    assert xray_file.exists()
    with open(xray_file) as f:
        data = json.load(f)

    assert len(data['tests']) == 4
    assert {test['testKey'] for test in data['tests']} == {'JIRA-1', 'JIRA-2', 'JIRA-3', 'JIRA-4'}


def test_jira_xray_plugin_multiple_ids_fail(xray_tests_multi_fail):
    xray_file = xray_tests_multi_fail.tmpdir.join('xray.json')
    result = xray_tests_multi_fail.runpytest('--jira-xray', '--xraypath', str(xray_file))
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(
        [
            '*Generated XRAY execution report file:*xray.json*',
        ]
    )
    assert result.ret == 1
    assert xray_file.exists()
    with open(xray_file) as f:
        data = json.load(f)

    assert len(data['tests']) == 2


@pytest.mark.parametrize('extra_args', ['-n 0', '-n 2'], ids=['no_xdist', 'xdist'])
def test_xray_with_all_test_types(testdir, extra_args):
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest

        @pytest.fixture
        def error_fixture():
            assert False

        @pytest.mark.xray('JIRA-1')
        def test_pass_status():
            assert True

        @pytest.mark.xray('JIRA-2')
        def test_fail_status():
            assert False

        @pytest.mark.xray('JIRA-3')
        def test_error_in_setup(error_fixture):
            assert True

        @pytest.mark.xray('JIRA-4')
        @pytest.mark.skip("skipping this test")
        def test_skip_status():
            assert True

        @pytest.mark.xray('JIRA-5')
        @pytest.mark.xfail(reason='expected fail')
        def test_xfail_status():
            assert False

        @pytest.mark.xray('JIRA-6')
        @pytest.mark.xfail(reason='expected fail')
        def test_xpass_status():
            assert True
        """
        )
    )
    report_file = testdir.tmpdir / 'xray.json'

    result = testdir.runpytest('--jira-xray', f'--xraypath={report_file}', '-v', extra_args)

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
        ('JIRA-6', 'PASS'),
    }


def test_if_tests_without_xray_id_are_not_included(testdir):
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest

        @pytest.mark.xray('JIRA-1')
        def test_pass():
            assert True

        def test_pass_without_id():
            assert True
        """
        )
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
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest

        @pytest.mark.xray('JIRA-1')
        def test_pass():
            assert True

        @pytest.mark.xray('JIRA-1')
        def test_pass_2():
            assert False
        """
        )
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


def test_add_captures(testdir):
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import logging
        import sys

        import pytest

        @pytest.mark.xray('JIRA-1')
        def test_pass():
            print('to stdout')
            print('to stderr', file=sys.stderr)
            logging.warning('to logger')
            assert True
        """
        )  # noqa: W293,W291
    )
    report_file = testdir.tmpdir / 'xray.json'

    expected_tests = [
        {
            'testKey': 'JIRA-1',
            'status': 'PASS',
            'comment': '{noformat:borderWidth=0px|bgColor=transparent}'
            '----------------------------- Captured stdout call -----------------------------\n'
            'to stdout\n'
            '----------------------------- Captured stderr call -----------------------------\n'
            'to stderr\n'
            '------------------------------ Captured log call -------------------------------\n'
            'WARNING  root:test_add_captures.py:10 to logger{noformat}',
        }
    ]

    result = testdir.runpytest('--jira-xray', f'--xraypath={report_file}', '--add-captures', '-v')
    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1)

    assert report_file.exists()
    with open(report_file) as file:
        data = json.load(file)
    assert data['tests'] == expected_tests


def test_defects(testdir):
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest

        @pytest.mark.xray('JIRA-1', defects=['BUG-1'])
        def test_single_defect():
            assert True

        @pytest.mark.xray('JIRA-2', defects=['BUG-2', 'BUG-3'])
        def test_multiple_defects():
            assert True

        @pytest.mark.xray('JIRA-3')
        def test_no_defects():
            assert True
        """
        )
    )

    report_file = testdir.tmpdir / 'xray.json'

    result = testdir.runpytest(
        '--jira-xray',
        f'--xraypath={report_file}',
        '-v',
    )

    assert result.ret == 0
    result.assert_outcomes(passed=3)
    assert report_file.exists()
    with open(report_file) as file:
        data = json.load(file)

    xray_defects = {t['testKey']: t.get('defects') for t in data['tests']}
    assert xray_defects == {
        'JIRA-1': ['BUG-1'],
        'JIRA-2': ['BUG-2', 'BUG-3'],
        'JIRA-3': None,
    }


def test_jira_xray_plugin_gets_unexpected_response(xray_tests, fake_xray_server):
    response = {'dummy': 'data'}
    with mock.patch('pytest_xray.xray_publisher.XrayPublisher._send_data', return_value=response):
        result = xray_tests.runpytest('--jira-xray', '--log-level=DEBUG', '-o', 'log_cli=1')
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            '*Cannot read Test Execution ID from server response*',
            '*Server response can be found in log file*',
        ]
    )
    assert result.ret == 0


def test_jira_xray_plugin_authentication_issue(xray_tests, environment_variables):
    with mock.patch('requests.post', side_effect=requests.exceptions.ConnectionError):
        result = xray_tests.runpytest('--jira-xray', '--client-secret-auth')
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            '*Could not publish results to Jira XRAY!*',
            '*ConnectionError: cannot authenticate with http://127.0.0.1:5002/api/v2/authenticate*',
        ]
    )
    assert result.ret == 0


def test_jira_xray_plugin_connection_error(xray_tests, environment_variables):
    with mock.patch('requests.request', side_effect=requests.exceptions.ConnectionError):
        result = xray_tests.runpytest('--jira-xray', '--client-secret-auth')
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            '*Could not publish results to Jira XRAY!*',
            '*ConnectionError: cannot connect to JIRA service at http://127.0.0.1:5002/rest/raven/2.0/import/execution*',
        ]
    )
    assert result.ret == 0


def test_jira_xray_plugin_http_error(xray_tests, fake_xray_server):
    response = mock.Mock(spec=requests.Response)
    response.status_code = 404
    response.json = mock.Mock(return_value={'error': 'Not Found for url'})
    response.raise_for_status.side_effect = requests.exceptions.HTTPError
    with mock.patch('requests.request', return_value=response):
        result = xray_tests.runpytest('--jira-xray')
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            '*Could not publish results to Jira XRAY!*',
            '*HTTPError: Could not post to JIRA service at http://127.0.0.1:5002/rest/raven/2.0/import/execution*',
            '*Error message from server: Not Found for url*',
        ]
    )
    assert result.ret == 0


def test_export_to_file_when_cannot_serialize_report(xray_tests):
    xray_tests.makeconftest(
        textwrap.dedent("""
        def pytest_xray_results(results, session):
            results['info']['revision'] = object()
    """)
    )
    report_file = xray_tests.tmpdir / 'jira.json'
    result = xray_tests.runpytest('--jira-xray', f'--xraypath={report_file}')
    assert result.ret == 0
    result.stdout.fnmatch_lines(['Cannot export Xray results to file: Object of type object is not JSON serializable'])
