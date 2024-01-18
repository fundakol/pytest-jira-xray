import json
import textwrap

import pytest


CONFTEST_CONTENT: str = textwrap.dedent("""
    from pytest_xray import evidence
    import pytest

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(item, call):
        outcome = yield
        report = outcome.get_result()
        evidences = getattr(report, "evidences", [])
        if report.when == "call":
            evidences.append(evidence.text(data="INFO: test", filename=f"test.log"))
            report.evidences = evidences
""")


def test_attach_evidence_for_tests(pytester: pytest.Pytester):
    expected_xray_report = {
        'info': {
            'finishDate': '2023-10-18T18:34:50+0000',
            'startDate': '2023-10-18T18:34:50+0000',
            'summary': 'Execution of automated tests'
        },
        'tests': [
            {
                'evidences': [
                    {
                        'contentType': 'text/plain',
                        'data': 'SU5GTzogdGVzdA==',
                        'filename': 'test.log'
                    }
                ],
                'status': 'PASS',
                'testKey': 'JIRA-1'
            }
        ]
    }

    pytester.makepyfile(textwrap.dedent("""
        import pytest

        @pytest.mark.xray('JIRA-1')
        def test_foo():
            assert True
    """))

    pytester.makeconftest(CONFTEST_CONTENT)

    report_file = pytester.path / 'xray.json'

    result = pytester.runpytest(
        '--jira-xray',
        '--allow-duplicate-ids',
        f'--xraypath={report_file}',
    )

    result.assert_outcomes(passed=1)
    assert report_file.exists()
    with open(report_file) as file:
        xray_report = json.load(file)

    assert xray_report['tests'] == expected_xray_report['tests']


@pytest.mark.xfail(reason='Bug')
def test_attach_evidence_for_tests_with_duplicated_ids(pytester: pytest.Pytester):
    expected_xray_report = {
        'info': {
            'finishDate': '2023-10-18T18:34:50+0000',
            'startDate': '2023-10-18T18:34:50+0000',
            'summary': 'Execution of automated tests'
        },
        'tests': [
            {
                'evidences': [
                    {
                        'contentType': 'plain/text',
                        'data': 'SU5GTzogdGVzdA==',
                        'filename': 'test.log'
                    },
                    {
                        'contentType': 'plain/text',
                        'data': 'SU5GTzogdGVzdA==',
                        'filename': 'test.log'
                    }
                ],
                'status': 'PASS',
                'testKey': 'JIRA-1'
            },
            {
                'evidences': [
                    {
                        'contentType': 'plain/text',
                        'data': 'SU5GTzogdGVzdA==',
                        'filename': 'test.log'
                    }
                ],
                'status': 'PASS',
                'testKey': 'JIRA-2'
            }
        ]
    }

    pytester.makepyfile(textwrap.dedent("""
        import pytest

        @pytest.mark.xray('JIRA-1')
        def test_foo():
            assert True

        @pytest.mark.xray('JIRA-1')
        def test_bar():
            assert True

        @pytest.mark.xray('JIRA-2')
        def test_baz():
            assert True
    """))

    pytester.makeconftest(CONFTEST_CONTENT)

    report_file = pytester.path / 'xray.json'

    result = pytester.runpytest(
        '--jira-xray',
        '--allow-duplicate-ids',
        f'--xraypath={report_file}',
    )

    result.assert_outcomes(passed=3)
    assert report_file.exists()
    with open(report_file) as file:
        xray_report = json.load(file)

    assert xray_report['tests'] == expected_xray_report['tests']
