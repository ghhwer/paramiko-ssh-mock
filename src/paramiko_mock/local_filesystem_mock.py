"""
This submodule implements the LocalFilesystemMock and LocalFileMock classes.
"""

from typing import Any


class LocalFileMock():
    """
    This class mocks a file in the local filesystem.
    """
    write_history: list[Any] = []
    file_content: Any = None

    def write(self, data: Any) -> None:
        self.write_history.append(data)
        if self.file_content is None:
            self.file_content = data
        else:
            self.file_content += data


# SFTPFileSystem is a class that stores the file system for the SFTPClientMock
class LocalFilesystemMock():
    """
    LocalFilesystemMock is a class that stores the mocked local filesystem.
    __This is mainly an internal class and should not be used directly.__
    """
    file_system: dict[str, LocalFileMock] = {}

    def add_file(self, path: str, file_mock: LocalFileMock) -> None:
        self.file_system[path] = file_mock

    def get_file(self, path: str) -> LocalFileMock | None:
        return self.file_system.get(path)

    def remove_file(self, path: str) -> None:
        self.file_system.pop(path, None)
