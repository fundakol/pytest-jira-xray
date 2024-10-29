import json
import logging
from pathlib import Path

from pytest_xray.exceptions import XrayError


logger = logging.getLogger(__name__)


class FilePublisher:
    """Exports Xray report to a file."""

    def __init__(self, filepath: str) -> None:
        self.filepath: Path = Path(filepath)

    def publish(self, data: dict) -> str:
        """
        Save results to a file or raise XrayError.

        :param data: data to save
        :return: file path where data was saved
        """
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.filepath, 'w', encoding='UTF-8') as file:
                json.dump(data, file, indent=2)
        except TypeError as exc:
            logger.exception(exc)
            raise XrayError(f'Cannot export Xray results to file: {exc}') from exc
        else:
            return f'{self.filepath}'
