# pytest-jira-xray

A plugin for pytest to integrate test results with JIRA Xray.

### Installation

```commandline
python setup.py install
```

### Usage

```python
import pytest

@pytest.mark.xray('JIRA-1')
def test_one():
    assert True
```

```commandline
export XRAY_API_BASE_URL=<jira URL>
export XRAY_API_USER=<jria username>
export XRAY_API_PASSWORD=<user password>

pytest . --jira-xray TestExecutionId
```
