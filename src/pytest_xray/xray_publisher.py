import json
import logging
from typing import Union

import requests
from requests.auth import AuthBase

from pytest_xray.constant import TEST_EXEXUTION_ENDPOINT
from pytest_xray.helper import TestExecution

logging.basicConfig()
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)


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
        try:
            response = requests.request(method='POST', url=url, headers=headers, data=data, auth=auth)
        except requests.exceptions.ConnectionError as e:
            _logger.exception('ConnectionError to JIRA service %s', self.base_url)
            raise XrayError(e)
        else:
            try:
                response.raise_for_status()
            except Exception as e:
                _logger.error('Could not post to JIRA service %s. Response status code: %s',
                              self.base_url, response.status_code)
                raise XrayError(e)
            return response.json()

    def publish(self, test_execution: TestExecution) -> bool:
        try:
            result = self.publish_xray_results(self.endpoint_url, self.auth, test_execution.as_dict())
        except XrayError:
            _logger.error('Could not publish results to Jira XRAY')
            return False
        else:
            key = result['testExecIssue']['key']
            _logger.info('Uploaded results to JIRA XRAY Test Execution: %d', key)
            return True
