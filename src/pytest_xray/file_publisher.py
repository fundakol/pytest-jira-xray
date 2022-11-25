import json
import logging
from pathlib import Path

from pytest_xray.exceptions import XrayError


logger = logging.getLogger(__name__)


class FilePublisher:

    def __init__(self, filepath: str):
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
        except TypeError as e:
            logger.exception(e)
            raise XrayError(f'Cannot save data to file: {self.filepath}') from e
        else:
            return f'{self.filepath}'
