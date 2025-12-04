import time
import os
from pathlib import Path
from typing import Any, Callable, Optional
from paramiko import SFTPAttributes
from .local_filesystem_mock import LocalFileMock, LocalFilesystemMock
from .exceptions import BadSetupError


# SFTPFileSystem is a class that stores the file system for the SFTPClientMock
class SFTPFileSystem():
    """
    The SFPTFileSystem class stores the file system for the SFTPClientMock.
    __This is mainly an internal class and should not be used directly.__
    """
    file_system: dict[str, "SFTPFileMock"] = {}

    def add_file(self, path: str, content: "SFTPFileMock") -> None:
        self.file_system[path] = content

    def get_file(self, path: str) -> Optional["SFTPFileMock"]:
        return self.file_system.get(path)

    def remove_file(self, path: str) -> None:
        self.file_system.pop(path, None)

    def list_files(self) -> list[str]:
        return list(self.file_system.keys())


class SFTPFileMock():
    """
    This class mocks a file in the remote filesystem.
    """
    write_history: list[Any] = []
    file_content: Any = None

    def close(self) -> None:
        pass

    def write(self, data: Any) -> None:
        self.write_history.append(data)
        self.file_content = data

    def read(self, size: int | None = None) -> Any:
        return self.file_content


class SFTPClientMock():
    """
    The SFTPClientMock class mocks the paramiko.SFTPClient class.
    __This is mainly an internal class and should not be used directly.__
    """

    def __init__(
        self,
        file_system: SFTPFileSystem | None = None,
        local_filesystem: LocalFilesystemMock | None = None
    ) -> None:
        if file_system is None:
            raise BadSetupError("file_system is required")
        if local_filesystem is None:
            raise BadSetupError("local_filesystem is required")
        self.__remote_file_system__: SFTPFileSystem = file_system
        self.__local_filesystem__: LocalFilesystemMock = local_filesystem

    def open(self, filename: str, mode: str = "r", bufsize: int = -1) -> "SFTPFileMock":
        file = self.__remote_file_system__.get_file(filename)
        if file is None:
            file = SFTPFileMock()
            self.__remote_file_system__.add_file(filename, file)
        return file

    def close(self) -> None:
        pass

    def put(
        self,
        localpath: str,
        remotepath: str,
        callback: Callable[[int, int], None] | None = None,
        prefetch: bool = True,
        max_concurrent_prefetch_requests: int | None = None,
        confirm: bool = True
    ) -> SFTPAttributes:
        mock_local_file = self.__local_filesystem__.get_file(localpath)
        if mock_local_file is None:
            raise FileNotFoundError(f"File not found: {localpath}")

        file_content = mock_local_file.file_content
        size = len(file_content)

        sftp_file_mock = SFTPFileMock()
        self.__remote_file_system__.add_file(remotepath, sftp_file_mock)

        chunk_size = 32768  # Typical SFTP chunk size
        transferred = 0

        for i in range(0, size, chunk_size):
            chunk = file_content[i:i + chunk_size]
            sftp_file_mock.write(chunk)
            transferred += len(chunk)
            if callback:
                callback(transferred, size)

        fake_stat = os.stat_result((
            33206,   # st_mode (file mode)
            1234567,  # st_ino (inode number)
            1000,    # st_dev (device)
            1,       # st_nlink (number of hard links)
            1001,    # st_uid (user ID of owner)
            1002,    # st_gid (group ID of owner)
            size,    # st_size (size in bytes)
            int(time.time()),  # st_atime (last access time)
            int(time.time()),  # st_mtime (last modification time)
            int(time.time())   # st_ctime (creation time on Windows,
                               # metadata change on Unix)
        ))

        if confirm:
            s = SFTPAttributes.from_stat(fake_stat)
            if s.st_size != size:
                raise IOError(f"size mismatch in put! {s.st_size} != {size}")
        else:
            s = SFTPAttributes()

        return s

    def get(
        self,
        remotepath: str,
        localpath: str,
        callback: Callable[[int, int], None] | None = None,
        prefetch: bool = True,
        max_concurrent_prefetch_requests: int | None = None
    ) -> None:
        file = self.__remote_file_system__.get_file(remotepath)
        if file is None:
            raise FileNotFoundError(f"File not found: {remotepath}")

        file_content = file.file_content
        size = len(file_content)

        local_file = LocalFileMock()
        self.__local_filesystem__.add_file(localpath, local_file)

        chunk_size = 32768  # Typical SFTP chunk size
        transferred = 0

        for i in range(0, size, chunk_size):
            chunk = file_content[i:i + chunk_size]
            local_file.write(chunk)
            transferred += len(chunk)
            if callback:
                callback(transferred, size)

    def listdir(self, path: str = ".") -> list[str]:
        file_path = Path(path)
        file_list = [Path(x) for x in self.__remote_file_system__.list_files()]
        return [x.name for x in file_list if x.parent == file_path]
