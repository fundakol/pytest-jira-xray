import base64
from typing import AnyStr, Dict

from pytest_xray.exceptions import XrayError


# Content Types
IMAGE_JPEG: str = 'image/jpeg'
IMAGE_PNG: str = 'image/png'
PLAIN_TEXT: str = 'plain/text'


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
        'ContentType': content_type
    }


def jpeg(data: AnyStr, filename: str) -> Dict[str, str]:
    return evidence(data, filename, IMAGE_JPEG)


def png(data: AnyStr, filename: str) -> Dict[str, str]:
    return evidence(data, filename, IMAGE_PNG)


def text(data: AnyStr, filename: str) -> Dict[str, str]:
    return evidence(data, filename, PLAIN_TEXT)
