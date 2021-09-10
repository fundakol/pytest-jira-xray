# pytest-jira-xray

[![PyPi](https://img.shields.io/pypi/v/pytest-jira-xray.png)](https://pypi.python.org/pypi/pytest-jira-xray)
[![Build Status](https://travis-ci.com/fundakol/pytest-jira-xray.svg?branch=master)](https://travis-ci.com/github/fundakol/pytest-jira-xray)

pytest-jira-xray is a plugin for pytest that uploads test results to JIRA XRAY.

### Installation

```commandline
pip install pytest-jira-xray
```

or

```commandline
python setup.py install
```

### Usage

Mark a test with JIRA XRAY test ID

```python
# -- FILE: test_example.py
import pytest

@pytest.mark.xray('JIRA-1')
def test_one():
    assert True
```

### Jira Xray configuration can be provided via Environment Variables:

* Jira base URL:
```commandline
$ export XRAY_API_BASE_URL=<Jira base URL>
```
- Basic authentication:
```commandline
$ export XRAY_API_USER=<jria username>
$ export XRAY_API_PASSWORD=<user password>
```

- SSL Client Certificate

To disable SSL certificate verification, at the client side (no case-sensitive), default is True: 
```commandline
$ export XRAY_API_VERIFY_SSL=False
```

Or you can provide path to certificate file
```commandline
$ export XRAY_API_VERIFY_SSL=</path/to/PEM file>
```

* Cloud authentication:
```commandline
$ export XRAY_CLIENT_ID=<client id>
$ export XRAY_CLIENT_SECRET=<client secret>
```

### Upload results 

* Upload results to new test execution:
```commandline
$ pytest --jira-xray
```

* Upload results to existing test execution:
```commandline
$ pytest --jira-xray --execution TestExecutionId
```

* Upload results to existing test plan (new test execution will be created):
```commandline
$ pytest --jira-xray --testplan TestPlanId
```

* Use with Jira cloud:
```commandline
$ pytest --jira-xray --cloud
```
