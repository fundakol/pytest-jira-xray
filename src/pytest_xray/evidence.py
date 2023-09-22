import base64
from pathlib import Path
from typing import AnyStr, Callable, Dict, Union

import pytest

from pytest_xray.exceptions import XrayError


# Content Types
IMAGE_JPEG: str = 'image/jpeg'
IMAGE_PNG: str = 'image/png'
TEXT_PLAIN: str = 'text/plain'
TEXT_HTML: str = 'text/html'
APP_JSON: str = 'application/json'
APP_ZIP: str = 'application/zip'


def evidence(data: AnyStr, filename: str, content_type: str) -> Dict[str, str]:
    if isinstance(data, bytes):
        data_base64: str = base64.b64encode(data).decode('utf-8')
    elif isinstance(data, str):
        data_base64 = base64.b64encode(data.encode('utf-8')).decode('utf-8')
    else:
        raise XrayError('data must be string or bytes')

    return {
        'data': data_base64,
        'filename': filename,
        'contentType': content_type
    }


def jpeg(data: AnyStr, filename: str) -> Dict[str, str]:
    return evidence(data, filename, IMAGE_JPEG)


def png(data: AnyStr, filename: str) -> Dict[str, str]:
    return evidence(data, filename, IMAGE_PNG)


def text(data: AnyStr, filename: str) -> Dict[str, str]:
    return evidence(data, filename, TEXT_PLAIN)


def html(data: AnyStr, filename: str) -> Dict[str, str]:
    return evidence(data, filename, TEXT_HTML)


def json(data: AnyStr, filename: str) -> Dict[str, str]:
    return evidence(data, filename, APP_JSON)


def zip(data: AnyStr, filename: str) -> Dict[str, str]:
    return evidence(data, filename, APP_ZIP)


@pytest.fixture
def xray_evidence(request) -> Callable:
    """ Fixture to add an evidence to the Test Run details of a Test.

    Copyright © 2023 Orange - All rights reserved
    """
    media_types = {
        'bin': 'application/octet-stream',
        'csv': 'text/csv',
        'gz': 'application/gzip',
        'html': 'text/html',
        'json': 'application/json',
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'js': 'text/javascript',
        'md': 'text/markdown',
        'pcap': 'application/vnd.tcdump.pcap',
        'png': 'image/png',
        'spdx': 'text/spdx',
        'txt': 'text/plain',
        'xml': 'text/xml',
        'yml': 'application/yaml',
        'yaml': 'application/yaml',
        'zip': 'application/zip'
    }

    def wrapper_evidence(path: Union[str, Path],
                         *, data: Union[str, bytes] = '',
                         ctype: str = ''
                         ) -> None:
        if (not isinstance(path, (str, Path)) or path == ''):
            raise XrayError('Missing path to evidence file')
        evidence_path: Path = Path(path)
        # Jira wants just a name for the attachment
        evidence_name = evidence_path.name

        if data == '':
            try:
                with open(evidence_path, 'rb') as f:
                    data_base64 = base64.b64encode(f.read())
            except OSError:
                raise XrayError(f'Cannot open or read file {evidence_path}')
        elif isinstance(data, bytes):
            data_base64 = base64.b64encode(data)
        else:
            data_base64 = base64.b64encode(bytes(data, encoding='utf-8'))

        if ctype == '':
            extension = evidence_path.suffix[1:]
            if media_types.get(extension) is None:
                contentType = 'application/octet-stream'
            else:
                contentType = str(media_types.get(extension))
        else:
            contentType = ctype

        new_evidence = {
            'data': data_base64.decode('utf-8'),
            'filename': evidence_name,
            'contentType': contentType
        }

        if not hasattr(request.node, 'evidences'):
            request.node.evidences = []
        request.node.evidences.append(new_evidence)

    return wrapper_evidence
