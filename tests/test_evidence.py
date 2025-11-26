import pytest

from pytest_xray.evidence import evidence
from pytest_xray.exceptions import XrayError


def test_if_evidence_return_proper_dict_for_string():
    assert evidence('text', 'file.txt', 'text/plain') == {
        'data': 'dGV4dA==',
        'filename': 'file.txt',
        'contentType': 'text/plain',
    }


def test_if_evidence_return_proper_dict_for_bytes():
    assert evidence(b'text', 'file.txt', 'text/plain') == {
        'data': 'dGV4dA==',
        'filename': 'file.txt',
        'contentType': 'text/plain',
    }


def test_if_evidence_raises_an_exception_for_unsuported_content():
    with pytest.raises(XrayError, match='data must be string or bytes'):
        evidence(10, 'file.txt', 'text/plain')  # type: ignore
