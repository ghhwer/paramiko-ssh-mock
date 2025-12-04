from .metaclasses import SingletonMeta
from .exceptions import BadSetupError

from .sftp_mock import SFTPFileSystem, SFTPFileMock
from .local_filesystem_mock import LocalFileMock, LocalFilesystemMock

# Import only for type hinting
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .ssh_mock import SSHResponseMock


class MockRemoteDevice:
    def __init__(
        self,
        host: str,
        port: int,
        responses: dict[str, 'SSHResponseMock'],
        local_filesystem: LocalFilesystemMock,
        username: Union[str, None] = None,
        password: Union[str, None] = None
    ) -> None:
        self.host: str = host
        self.port: int = port
        self.responses: dict[str, 'SSHResponseMock'] = responses
        self.username: Union[str, None] = username
        self.password: Union[str, None] = password
        self.filesystem: SFTPFileSystem = SFTPFileSystem()
        self.local_filesystem: LocalFilesystemMock = local_filesystem
        self.command_history: list[str] = []

    def authenticate(self, username: str, password: str) -> bool:
        if self.username is None and self.password is None:
            return True
        return (self.username, self.password) == (username, password)

    def clear(self) -> None:
        self.command_history.clear()

    def add_command_to_history(self, command: str) -> None:
        self.command_history.append(command)


# ParamikoMockEnviron is a Singleton class
# that stores the responses for the SSHClientMock
class ParamikoMockEnviron(metaclass=SingletonMeta):
    """
    This class is the Coordinator for the ParamikoMock environment.
    It stores information about the remote devices and the local filesystem.
    """

    def __init__(self) -> None:
        self.__remote_devices__: dict[str, 'MockRemoteDevice'] = {}
        # Local filesystem
        self.__local_filesystem__: "LocalFilesystemMock" = LocalFilesystemMock()

    # Private/protected methods
    def _get_remote_device(self, host: str) -> 'MockRemoteDevice':
        """
        `_get_remote_device` is a method that retrieves a remote device from the
        environment.

        - host: The hostname of the remote device.
        Returns: The remote device.

        _Note: This method is protected and should not be used outside of the
        package._ (We cannot guarantee that this method will not change in the
        future)
        """
        return self.__remote_devices__.get(host) or (_ for _ in ()).throw(
            BadSetupError(
                'Remote device not registered, did you forget to call '
                'add_responses_for_host?'
            )
        )

    # Public methods

    def add_responses_for_host(
        self,
        host: str,
        port: int,
        responses: dict[str, 'SSHResponseMock'],
        username: Union[str, None] = None,
        password: Union[str, None] = None
    ) -> None:
        """
        `add_responses_for_host` is a method that adds responses for a remote
        device. Effectively, it creates a new MockRemoteDevice object and stores
        it in the environment.

        - host: The hostname of the remote device.
        - port: The port of the remote device.
        - responses: A dictionary that maps commands to responses.
        - username: The username for the remote device (optional)
        - password: The password for the remote device (optional)
        """
        self.__remote_devices__[f'{host}:{port}'] = MockRemoteDevice(
            host, port, responses, self.__local_filesystem__,
            username, password
        )

    def cleanup_environment(self) -> None:
        """
        `cleanup_environment` is a method that clears the environment.
        """
        # Clear all the responses, credentials and filesystems
        self.__remote_devices__.clear()
        self.__local_filesystem__.file_system.clear()

    def add_mock_file_for_host(
        self,
        host: str,
        port: int,
        path: str,
        file_mock: 'SFTPFileMock'
    ) -> None:
        """
        `add_mock_file_for_host` is a method that adds a mock file to the remote
        filesystem for a specific host.

        - host: The hostname of the remote device.
        - port: The port of the remote device.
        - path: The path of the file.
        - file_mock: The mock file to add.
        """
        device = self._get_remote_device(f'{host}:{port}')
        device.filesystem.add_file(path, file_mock)

    def remove_mock_file_for_host(self, host: str, port: int, path: str) -> None:
        """
        `remove_mock_file_for_host` is a method that removes a mock file from the
        remote filesystem for a specific host.

        - host: The hostname of the remote device.
        - port: The port of the remote device.
        - path: The path of the file.
        """
        device = self._get_remote_device(f'{host}:{port}')
        device.filesystem.remove_file(path)

    def get_mock_file_for_host(self, host: str, port: int, path: str) -> 'SFTPFileMock':
        """
        `get_mock_file_for_host` is a method that retrieves a mock file from the
        remote filesystem for a specific host.

        - host: The hostname of the remote device.
        - port: The port of the remote device.
        - path: The path of the file.

        Returns: The mock file.
        """
        device = self._get_remote_device(f'{host}:{port}')
        return device.filesystem.get_file(path)

    def add_local_file(self, path: str, file_mock: 'LocalFileMock') -> None:
        """
        `add_local_file` is a method that adds a mock file to the local
        filesystem.

        - path: The path of the file.
        - file_mock: The mock file to add.
        """
        self.__local_filesystem__.add_file(path, file_mock)

    def remove_local_file(self, path: str) -> None:
        """
        `remove_local_file` is a method that removes a mock file from the local
        filesystem.

        - path: The path of the file.
        """
        self.__local_filesystem__.remove_file(path)

    def get_local_file(self, path: str) -> 'LocalFileMock':
        """
        `get_local_file` is a method that retrieves a mock file from the local
        filesystem.

        - path: The path of the file.

        Returns: The mock file.
        """
        return self.__local_filesystem__.get_file(path)

    # Asserts
    def assert_command_was_executed(self, host: str, port: int, command: str) -> None:
        """
        `assert_command_was_executed` is a method that asserts that a command
        was executed

        - host: The hostname of the remote device.
        - port: The port of the remote device.
        - command: The command to assert.

        Raises: AssertionError if the command was not executed.
        """
        device = self._get_remote_device(f'{host}:{port}')
        assert command in device.command_history

    def assert_command_was_not_executed(
        self,
        host: str,
        port: int,
        command: str
    ) -> None:
        """
        `assert_command_was_not_executed` is a method that asserts that a
        command was not executed

        - host: The hostname of the remote device.
        - port: The port of the remote device.
        - command: The command to assert.

        Raises: AssertionError if the command was executed
        """
        device = self._get_remote_device(f'{host}:{port}')
        assert command not in device.command_history

    def assert_command_executed_on_index(
        self,
        host: str,
        port: int,
        command: str,
        index: int
    ) -> None:
        """
        `assert_command_executed_on_index` is a method that asserts that a
        command was executed on a specific index

        - host: The hostname of the remote device.
        - port: The port of the remote device.
        - command: The command to assert.
        - index: The index to assert.

        Raises: AssertionError if the command was not executed on the index.
        """
        device = self._get_remote_device(f'{host}:{port}')
        assert device.command_history[index] == command
