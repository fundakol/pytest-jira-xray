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


@pytest.fixture()
def xray_tests_evidence(testdir):
    """
    Copyright © 2023 Orange - All rights reserved
    """
    localfile = Path(testdir.makefile('.txt', test='Test')).name
    emptyfile = testdir.makefile('.txt', empty='')
    test_example = textwrap.dedent(f"""\
        import pytest
        from pytest_xray.exceptions import XrayError

        @pytest.mark.xray('JIRA-1')
        def test_pass(evidence):
            evidence(path="data.txt", data="Test", ctype="text/plain")
            evidence(path="data.bin", data=b"Test\\xb6", ctype="application/octet-stream")
            evidence(data="Test")
            evidence(data=b"Test\\xb6")
            evidence(data="<h1>Test</h1>", ctype="text/html")
            evidence("{RESOURCE_DIR}/screenshot.png")
            evidence("{localfile}")
            evidence("{emptyfile}")
            evidence(data="--Test", ctype="text/prs.testing")
            with pytest.raises(XrayError):
                evidence(ctype="text/plain")            # data or path missing
            with pytest.raises(XrayError):
                evidence(path=b"test.txt")              # path is not 'str'
            with pytest.raises(XrayError):
                evidence("{RESOURCE_DIR}/test.xyz")     # unknown media type / ctype missing
            with pytest.raises(XrayError):
                evidence("{RESOURCE_DIR}/testt.txt")    # file not found
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
        '*--cloud*Use with JIRA XRAY cloud server*',
        '*--api-key-auth*Use Jira API Key authentication*',
        '*--client-secret-auth*Use client secret authentication*',
        '*--execution=ExecutionId*', '*XRAY Test Execution ID*',
        '*--testplan=TestplanId*', '*XRAY Test Plan ID*',
        '*--xraypath=path*Do not upload to a server but create JSON report file at*', '*given path*',
        '*--allow-duplicate-ids*', '*Allow test ids to be present on multiple pytest tests*',
        '*--add-captures*Add captures from log, stdout or/and stderr, to the*', '*report comment field*',
    ])


@pytest.mark.parametrize(
    'cli_options',
    [
        ('--jira-xray',),
        ('--jira-xray', '--cloud', '--client-secret-auth'),
        ('--jira-xray', '--cloud', '--api-key-auth')
    ],
    ids=['DC Server', 'Cloud client secret', 'Cloud api key']
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


def test_if_user_can_attach_evidences(xray_tests_evidence):
    expected_tests = [
        {'testKey': 'JIRA-1',
         'status': 'PASS',
         'evidences': [
             {'data': 'VGVzdA==',
              'filename': 'data.txt',
              'contentType': 'text/plain'},
             {'data': 'VGVzdLY=',
                 'filename': 'data.bin',
                 'contentType': 'application/octet-stream'},
             {'data': 'VGVzdA==',
                 'filename': 'attachment1.txt',
                 'contentType': 'text/plain'},
             {'data': 'VGVzdLY=',
                 'filename': 'attachment2.bin',
                 'contentType': 'application/octet-stream'},
             {'data': 'PGgxPlRlc3Q8L2gxPg==',
                 'filename': 'attachment3.html',
                 'contentType': 'text/html'},
             {'data': 'iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAH0lEQVQIW2OcNm3afwY0wEi+ID'
                 '8/PwOKdpCAjIwMAwBGOw558x9CSQAAAABJRU5ErkJggg==',
                 'filename': 'screenshot.png',
                 'contentType': 'image/png'},
             {'data': 'VGVzdA==',
                 'filename': 'test.txt',
                 'contentType': 'text/plain'},
             {'data': '',
                 'filename': 'empty.txt',
                 'contentType': 'text/plain'},
             {'data': 'LS1UZXN0',
                 'filename': 'attachment4',
                 'contentType': 'text/prs.testing'}
         ]}
    ]

    xray_file = xray_tests_evidence.tmpdir.join('xray.json')
    result = xray_tests_evidence.runpytest('--jira-xray', '--xraypath', str(xray_file))
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


@pytest.mark.parametrize('extra_args', ['-n 0', '-n 2'], ids=['no_xdist', 'xdist'])
def test_xray_with_all_test_types(testdir, extra_args):
    testdir.makepyfile(textwrap.dedent(
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
        """))
    report_file = testdir.tmpdir / 'xray.json'

    result = testdir.runpytest(
        '--jira-xray',
        f'--xraypath={report_file}',
        '-v',
        extra_args
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


def test_add_captures(testdir):
    testdir.makepyfile(textwrap.dedent(
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
        """)  # noqa: W293,W291
        )
    report_file = testdir.tmpdir / 'xray.json'

    expected_tests = [
        {'testKey': 'JIRA-1',
         'status': 'PASS',
         'comment': '{noformat:borderWidth=0px|bgColor=transparent}'
            '----------------------------- Captured stdout call -----------------------------\n'
            'to stdout\n'
            '----------------------------- Captured stderr call -----------------------------\n'
            'to stderr\n'
            '------------------------------ Captured log call -------------------------------\n'
            'WARNING  root:test_add_captures.py:10 to logger{noformat}'}
    ]

    result = testdir.runpytest(
        '--jira-xray',
        f'--xraypath={report_file}',
        '--add-captures',
        '-v'
    )
    assert result.ret == pytest.ExitCode.OK
    result.assert_outcomes(passed=1)

    assert report_file.exists()
    with open(report_file) as file:
        data = json.load(file)
    assert data['tests'] == expected_tests
