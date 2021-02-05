import json
from typing import Union

import requests
from pytest_xray.constant import TEST_EXEXUTION_ENDPOINT
from pytest_xray.helper import TestExecution
from requests.auth import AuthBase


class XrayError(Exception):
    """Custom exception for Jira XRAY"""


class XrayPublisher:

    def __init__(self, base_url: str, auth: Union[AuthBase, tuple]) -> None:
        self.base_url = base_url
        self.auth = auth

    @property
    def endpoint_url(self) -> str:
        return self.base_url + TEST_EXEXUTION_ENDPOINT

    def publish_xray_results(self, url: str, auth: AuthBase, data: dict) -> dict:
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json'}
        data = json.dumps(data)
        response = requests.request(method='POST', url=url, headers=headers, data=data, auth=auth)
        try:
            response.raise_for_status()
        except Exception as e:
            raise XrayError(e)
        return response.json()

    def publish(self, test_execution: TestExecution) -> None:
        try:
            self.publish_xray_results(self.endpoint_url, self.auth, test_execution.as_dict())
        except XrayError as e:
            print('Could not publish to Jira:', e)
