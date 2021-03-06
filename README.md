# pytest-jira-xray

pytest-jira-xray is a plugin for pytest that uploads test results to JIRA XRAY.

### Installation

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

Set system environment:
```commandline
export XRAY_API_BASE_URL=<jira URL>
export XRAY_API_USER=<jria username>
export XRAY_API_PASSWORD=<user password>
```

Upload results to new test execution:
```commandline
pytest . --jira-xray
```

Upload results to existing test execution:
```commandline
pytest . --jira-xray --execution TestExecutionId
```

Upload results to existing test plan (new test execution will be created):
```commandline
pytest . --jira-xray --testplan TestPlanId
```
