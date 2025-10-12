from typing import Any

import pytest


@pytest.hookspec
def pytest_xray_results(results: dict[str, Any], session: pytest.Session) -> None:
    """
    Called before uploading XRAY result to Jira server.

    :param results: xray results dictionary
    :param session: pytest session
    """
