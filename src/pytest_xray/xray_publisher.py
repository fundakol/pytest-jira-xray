import logging
from typing import Union

import requests
from requests.auth import AuthBase

from pytest_xray.constant import TEST_EXECUTION_ENDPOINT
from pytest_xray.helper import TestExecution

_logger = logging.getLogger(__name__)


class XrayError(Exception):
    """Custom exception for Jira XRAY"""


class XrayPublisher:

    def __init__(self,
                 base_url: str,
                 auth: Union[AuthBase, tuple],
                 verify: Union[bool, str] = True) -> None:
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.auth = auth
        self.verify = verify

    @property
    def endpoint_url(self) -> str:
        return self.base_url + TEST_EXECUTION_ENDPOINT

    def publish_xray_results(self, url: str, auth: AuthBase, data: dict) -> dict:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.request(method='POST', url=url, headers=headers, json=data,
                                        auth=auth, verify=self.verify)
        except requests.exceptions.ConnectionError as e:
            _logger.exception('ConnectionError to JIRA service %s', self.base_url)
            raise XrayError(e)
        else:
            try:
                response.raise_for_status()
            except Exception as e:
                _logger.error('Could not post to JIRA service %s. Response status code: %s',
                              self.base_url, response.status_code)
                raise XrayError from e
            return response.json()

    def publish(self, test_execution: TestExecution) -> str:
        """
        Publish results to Jira.

        :param test_execution: instance of TestExecution class
        :return: test execution issue id
        """
        try:
            result = self.publish_xray_results(self.endpoint_url, self.auth, test_execution.as_dict())
        except XrayError:
            return ''
        else:
            key = result['testExecIssue']['key']
            _logger.info('Uploaded results to JIRA XRAY Test Execution: %s', key)
            return key
