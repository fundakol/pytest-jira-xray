================
pytest-jira-xray
================

.. image:: https://img.shields.io/pypi/v/pytest-jira-xray.png
   :target: https://pypi.python.org/pypi/pytest-jira-xray
   :alt: PyPi
.. image:: https://travis-ci.com/fundakol/pytest-jira-xray.svg?branch=master
   :target: https://travis-ci.com/github/fundakol/pytest-jira-xray
   :alt: Build status
.. image:: https://codecov.io/gh/fundakol/pytest-jira-xray/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/fundakol/pytest-jira-xray
   :alt: Code coverage


pytest-jira-xray is a plugin for pytest that uploads test results to JIRA XRAY.


Installation
------------

.. code-block::

    pip install pytest-jira-xray

or

.. code-block::

    python setup.py install


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


- Basic authentication:

.. code-block:: bash

    $ export XRAY_API_USER=<jria username>
    $ export XRAY_API_PASSWORD=<user password>

- API KEY

.. code-block:: bash

    $ export XRAY_API_KEY=<api key>

- SSL Client Certificate

To disable SSL certificate verification, at the client side (no case-sensitive), default is True: 

.. code-block:: bash

    $ export XRAY_API_VERIFY_SSL=False


Or you can provide path to certificate file

.. code-block:: bash

    $ export XRAY_API_VERIFY_SSL=</path/to/PEM file>


* Cloud authentication:

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

* Use with Jira API KEY:

.. code-block:: bash

    $ pytest --jira-xray --api-key

* Use with Jira cloud:

.. code-block:: bash

    $ pytest --jira-xray --cloud


* Store results in a file instead of exporting directly to a XRAY server

.. code-block:: bash

    $ pytest --jira-xray --xraypath=xray.json


IntelliJ integration
++++++++++++++++++++

When you want to synchronize your test results via. Pytest integration in IntelliJ, you need to configure the following:

1. Use the *pytest* test configuration template and add `--jira-xray -o log_cli=true` to *Additional Arguments*

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
