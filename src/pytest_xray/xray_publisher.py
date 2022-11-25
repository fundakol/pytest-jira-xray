import json
import logging
from typing import Union

import requests
from requests.auth import AuthBase

from pytest_xray.constant import AUTHENTICATE_ENDPOINT
from pytest_xray.exceptions import XrayError


_logger = logging.getLogger(__name__)


class ClientSecretAuth(AuthBase):
    """Bearer authentication with Client ID and a Client Secret."""

    def __init__(self, base_url: str, client_id: str, client_secret: str) -> None:
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret

    @property
    def endpoint_url(self) -> str:
        return f'{self.base_url}{AUTHENTICATE_ENDPOINT}'

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        headers = {
            'Content-type': 'application/json',
            'Accept': 'text/plain'
        }
        auth_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        try:
            response = requests.post(
                self.endpoint_url,
                data=json.dumps(auth_data),
                headers=headers
            )
        except requests.exceptions.ConnectionError as exc:
            err_message = f'ConnectionError: cannot authenticate with {self.endpoint_url}'
            _logger.exception(err_message)
            raise XrayError(err_message) from exc
        else:
            auth_token = response.text.replace('"', '')
            r.headers['Authorization'] = f'Bearer {auth_token}'
        return r


class ApiKeyAuth(AuthBase):
    """Personal access token authentication."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        r.headers['Authorization'] = f'Bearer {self.api_key}'
        return r


class XrayPublisher:

    def __init__(
        self,
        base_url: str,
        endpoint: str,
        auth: Union[AuthBase, tuple],
        verify: Union[bool, str] = True
    ) -> None:
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.endpoint = endpoint
        self.auth = auth
        self.verify = verify

    @property
    def endpoint_url(self) -> str:
        return self.base_url + self.endpoint

    def _send_data(self, url: str, auth: Union[AuthBase, tuple], data: dict) -> dict:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.request(
                method='POST', url=url, headers=headers, json=data,
                auth=auth, verify=self.verify
            )
        except requests.exceptions.ConnectionError as exc:
            err_message = f'ConnectionError: cannot connect to JIRA service at {url}'
            _logger.exception(err_message)
            raise XrayError(err_message) from exc
        else:
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as exc:
                err_message = (f'HTTPError: Could not post to JIRA service at {url}. '
                               f'Response status code: {response.status_code}')
                _logger.exception(err_message)
                if 'error' in response.json():
                    server_return_error = f"Error message from server: {response.json()['error']}"
                    err_message += '\n' + server_return_error
                    _logger.error(server_return_error)
                raise XrayError(err_message) from exc
            return response.json()

    def publish(self, data: dict) -> str:
        """
        Publish results to Jira and return testExecutionId or raise XrayError.

        :param data: data to send
        :return: test execution issue id
        """
        response_data = self._send_data(self.endpoint_url, self.auth, data)
        # The Xray cloud response does not include the 'testExecIssue' attribute
        key = response_data['testExecIssue']['key'] if 'testExecIssue' in response_data else response_data['key']
        return key
