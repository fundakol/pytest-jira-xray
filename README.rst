================
pytest-jira-xray
================

.. image:: https://img.shields.io/pypi/v/pytest-jira-xray.png
   :target: https://pypi.python.org/pypi/pytest-jira-xray
   :alt: PyPi
.. image:: https://github.com/fundakol/pytest-jira-xray/actions/workflows/main.yml/badge.svg?branch=master
   :target: https://github.com/fundakol/pytest-jira-xray/actions?query=workflow?master
   :alt: Build status
.. image:: https://codecov.io/gh/fundakol/pytest-jira-xray/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/fundakol/pytest-jira-xray
   :alt: Code coverage


pytest-jira-xray is a plugin for pytest that uploads test results to JIRA XRAY.


Installation
------------

Installing from pypi repository:

.. code-block::

    pip install -U pytest-jira-xray

Installing from local source:

.. code-block::

    pip install <path>

Installing from local source in development mode:

.. code-block::

    pip install -e <path>


Usage
-----

Mark a test with JIRA XRAY test ID or list of IDs

.. code-block:: python

    # -- FILE: test_example.py

    import pytest

    @pytest.mark.xray('JIRA-1')
    def test_foo():
        assert True

    @pytest.mark.xray(['JIRA-2', 'JIRA-3'])
    def test_bar():
        assert True


Jira Xray configuration can be provided via Environment Variables:
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

* Jira base URL:

.. code-block:: bash

    $ export XRAY_API_BASE_URL=<Jira base URL>


* Basic authentication with username and password (default)

.. code-block:: bash

    $ export XRAY_API_USER=<jria username>
    $ export XRAY_API_PASSWORD=<user password>

* Personal Access Token authentication (``--api-key-auth`` option)

.. code-block:: bash

    $ export XRAY_API_KEY=<api key>

* SSL Client Certificate

To disable SSL certificate verification, at the client side (no case-sensitive), default is True:

.. code-block:: bash

    $ export XRAY_API_VERIFY_SSL=False


Or you can provide path to certificate file

.. code-block:: bash

    $ export XRAY_API_VERIFY_SSL=</path/to/PEM file>


* Authentication with client ID and client secret (``--client-secret-auth`` option):

.. code-block:: bash

    $ export XRAY_CLIENT_ID=<client id>
    $ export XRAY_CLIENT_SECRET=<client secret>


* Test Execution parameters:

.. code-block:: bash

    $ export XRAY_EXECUTION_TEST_ENVIRONMENTS="Env1 Env2 Env3"
    $ export XRAY_EXECUTION_FIX_VERSION="1.0"
    $ export XRAY_EXECUTION_REVISION=`git rev-parse HEAD`

    $ export XRAY_EXECUTION_SUMMARY="Smoke tests" # New execution only
    $ export XRAY_EXECUTION_DESC="This is an automated test execution of the smoke tests" # New execution only


Upload results
++++++++++++++

* Upload results to new test execution:

.. code-block:: bash

    $ pytest --jira-xray


* Upload results to existing test execution:

.. code-block:: bash

    $ pytest --jira-xray --execution TestExecutionId


* Upload results to existing test plan (new test execution will be created):

.. code-block:: bash

    $ pytest --jira-xray --testplan TestPlanId


* Store results in a file instead of exporting directly to a XRAY server

.. code-block:: bash

    $ pytest --jira-xray --xraypath=xray.json


* Use with Jira cloud:

The Xray REST API may use two different endpoints: Server+DC or Cloud.
There is a difference between formats of test results (test status can be ``PASS`` or ``PASSED``),
so if you want to use this plugin with Xray Cloud endpoint you should run pytest with additional
argument ``--cloud``. This will generate test results with the format accepted by the Cloud service.

.. code-block:: bash

    $ pytest --jira-xray --cloud


Jira authentication
+++++++++++++++++++

* Jira `basic authentication <https://developer.atlassian.com/server/jira/platform/basic-authentication/>`_:

It is default authentication.


* Jira authentication with `Client ID and a Client Secret <https://docs.getxray.app/display/XRAYCLOUD/Authentication+-+REST+v2>`_:

.. code-block:: bash

    $ pytest --jira-xray --client-secret-auth


* Jira `Personal access tokens <https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html>`_ (API KEY) authentication:

.. code-block:: bash

    $ pytest --jira-xray --api-key-auth


Multiple ids support
++++++++++++++++++++

Tests can be marked to handle multiple Jira tests by adding a list, rather than a string. Example:

.. code-block:: python

    # -- FILE: test_example.py

    import pytest

    @pytest.mark.xray([
        'JIRA-1',
        'JIRA-2'
    ])
    def test_my_process():
        assert True

If the test fails, both JIRA-1 and JIRA-2 tests will be marked as fail. The
failure comment will contain the same message for both tests.

This situation can be useful for validation tests or tests that probe multiple
functionalities in a single run, to reduce execution time.

Duplicated ids support
++++++++++++++++++++++

By default, the jira-xray plugin does not allow to have multiple tests marked with
the same identifier, like in this case:

.. code-block:: python

    # -- FILE: test_example.py

    import pytest

    @pytest.mark.xray('JIRA-1')
    def test_my_process_1():
        assert True

    @pytest.mark.xray('JIRA-1')
    def test_my_process_2():
        assert True

However, depending how the user story and the associated test are formulated,
this scenario may be useful. The option ``--allow-duplicate-ids`` will perform the tests
even when duplicate ids are present. The JIRA-1 test result will be created according to
the following rules:

- The comment will be the comment from each of the test, separated by a horizontal divider.
- The status will be the intuitive combination of the individual results: if ``test_my_process_1``
  is a ``PASS`` but ``test_my_process_2`` is a ``FAIL``, ``JIRA-1`` will be marked as ``FAIL``.


Attach test evidences
+++++++++++++++++++++

The following example adds the test evidences to the Xray report
using a ``pytest_runtest_makereport`` hook.

.. code-block:: python

    # -- FILE: conftest.py

    import pytest
    from pytest_xray import evidence

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(item, call):
        outcome = yield
        report = outcome.get_result()
        evidences = getattr(report, "evidences", [])
        if report.when == "call":
            xfail = hasattr(report, "wasxfail")
            if (report.skipped and xfail) or (report.failed and not xfail):
                data = open("screenshot.jpeg", "rb").read()
                evidences.append(evidence.jpeg(data=data, filename="screenshot.jpeg"))
            report.evidences = evidences


Hooks
+++++

There is possibility to modify a XRAY report before it is send to a server by ``pytest_xray_results`` hook.

.. code-block:: python

    def pytest_xray_results(results, session):
        results['info']['user'] = 'pytest'


IntelliJ integration
++++++++++++++++++++

When you want to synchronize your test results via. Pytest integration in IntelliJ, you need to configure the following:

1. Use the *pytest* test configuration template and add ``--jira-xray -o log_cli=true`` to *Additional Arguments*

.. image:: https://user-images.githubusercontent.com/22340156/145638520-c6bf56d2-089e-430c-94ae-ac8122a3adea.png
   :target: https://user-images.githubusercontent.com/22340156/145638520-c6bf56d2-089e-430c-94ae-ac8122a3adea.png

2. Disable `--no-summary` in *Settings*

.. image:: https://user-images.githubusercontent.com/22340156/145638538-71590ec8-86c6-4b93-9a99-460b4e38e153.png
   :target: https://user-images.githubusercontent.com/22340156/145638538-71590ec8-86c6-4b93-9a99-460b4e38e153.png


Troubleshooting
+++++++++++++++

This section holds information about common issues.

`The Test XXX is in a non-executable status`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Problem: The test is not executable by the user.

* Solution: Make sure, that your test is not deactivated, approved and ready to use in Jira.

`Error message from server: fixVersions: fixVersions`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Problem: The version is malformed or doesn't exist.

* Solution: Make sure the version exists and the name matches the existing version and that only one version is used.


References
----------

- XRay import execution endpoint: `<https://docs.getxray.app/display/XRAY/Import+Execution+Results>`_
