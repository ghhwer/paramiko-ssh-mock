from .metaclasses import SingletonMeta
from .exceptions import BadSetupError

from .sftp_mock import SFTPFileSystem, SFTPFileMock
from .local_filesystem_mock import LocalFileMock, LocalFilesystemMock

import socket
from paramiko import BadHostKeyException
from paramiko.message import Message
from paramiko.pkey import PKey
from paramiko.ssh_exception import AuthenticationException

# Import only for type hinting
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ssh_mock import SSHResponseMock


class ConnectionFailureConfig:
    """
    Configuration class for different types of connection failures.
    This allows users to configure specific failure scenarios similar to the responses library.
    """

    @staticmethod
    def dns_failure(hostname: str = None):
        """Create a DNS resolution failure (socket.gaierror)"""
        if hostname is None:
            hostname = "unknown_host"
        return socket.gaierror(-2, f"Name or service not known: {hostname}")

    @staticmethod
    def timeout_failure():
        """Create a connection timeout failure (TimeoutError)"""
        return TimeoutError("timed out")

    @staticmethod
    def authentication_failure():
        """Create an authentication failure (AuthenticationException)"""
        return AuthenticationException("Authentication failed")

    @staticmethod
    def connection_refused():
        """Create a connection refused failure"""
        return ConnectionRefusedError("Connection refused")

    @staticmethod
    def bad_host_exception(
        hostname: str = None,
        custom_got_key: PKey | None = None,
        custom_pkey: PKey | None = None
    ):
        if hostname is None:
            hostname = "unknown_host"
        if custom_pkey is None:
            custom_pkey = PKey(
                msg=Message("MockedKey".encode()),
                data="MockedKeyData"
            )
        if custom_got_key is None:
            custom_got_key = PKey(
                msg=Message("MockedKey".encode()),
                data="MockedKeyData"
            )
        return BadHostKeyException(hostname, custom_got_key, custom_pkey)

    @staticmethod
    def custom_exception(exception):
        """Create a custom exception"""
        return exception


class MockRemoteDevice:
    def __init__(
        self,
        host: str,
        port: int,
        responses: dict[str, 'SSHResponseMock'],
        local_filesystem: LocalFilesystemMock,
        username: str | None = None,
        password: str | None = None,
        connection_failure: Exception | None = None
    ) -> None:
        self.host: str = host
        self.port: int = port
        self.responses: dict[str, 'SSHResponseMock'] = responses
        self.username: str | None = username
        self.password: str | None = password
        self.filesystem: SFTPFileSystem = SFTPFileSystem()
        self.local_filesystem: LocalFilesystemMock = local_filesystem
        self.command_history: list[str] = []
        self.connection_failure: Exception | None = connection_failure

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
    def get_remote_device(self, host: str) -> 'MockRemoteDevice':
        """
        `get_remote_device` is a method that retrieves a remote device from the
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
        username: str | None = None,
        password: str | None = None,
        connection_failure: Exception | None = None
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
        - connection_failure: An exception to raise during connection (optional)
        """
        self.__remote_devices__[f'{host}:{port}'] = MockRemoteDevice(
            host, port, responses, self.__local_filesystem__,
            username, password, connection_failure
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
        device = self.get_remote_device(f'{host}:{port}')
        device.filesystem.add_file(path, file_mock)

    def remove_mock_file_for_host(self, host: str, port: int, path: str) -> None:
        """
        `remove_mock_file_for_host` is a method that removes a mock file from the
        remote filesystem for a specific host.

        - host: The hostname of the remote device.
        - port: The port of the remote device.
        - path: The path of the file.
        """
        device = self.get_remote_device(f'{host}:{port}')
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
        device = self.get_remote_device(f'{host}:{port}')
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
        device = self.get_remote_device(f'{host}:{port}')
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
        device = self.get_remote_device(f'{host}:{port}')
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
        device = self.get_remote_device(f'{host}:{port}')
        assert device.command_history[index] == command

    # Connection failure setup methods
    def setup_dns_failure(self, host: str, port: int = 22, hostname: str = None) -> None:
        """
        Set up a DNS resolution failure for a host.

        - host: The hostname to fail DNS resolution for
        - port: The port (default: 22)
        - hostname: Optional custom hostname for the error message
        """
        self.add_responses_for_host(
            host, port, {},
            connection_failure=ConnectionFailureConfig.dns_failure(hostname)
        )

    def setup_timeout_failure(self, host: str, port: int = 22) -> None:
        """
        Set up a connection timeout failure for a host.

        - host: The hostname to timeout for
        - port: The port (default: 22)
        """
        self.add_responses_for_host(
            host, port, {},
            connection_failure=ConnectionFailureConfig.timeout_failure()
        )

    def setup_authentication_failure(self, host: str, port: int = 22) -> None:
        """
        Set up an authentication failure for a host.

        - host: The hostname to fail authentication for
        - port: The port (default: 22)
        """
        self.add_responses_for_host(
            host, port, {},
            connection_failure=ConnectionFailureConfig.authentication_failure()
        )

    def setup_connection_refused(self, host: str, port: int = 22) -> None:
        """
        Set up a connection refused failure for a host.

        - host: The hostname to refuse connection for
        - port: The port (default: 22)
        """
        self.add_responses_for_host(
            host, port, {},
            connection_failure=ConnectionFailureConfig.connection_refused()
        )

    def setup_custom_failure(self, host: str, port: int, exception: Exception) -> None:
        """
        Set up a custom exception failure for a host.

        - host: The hostname to fail for
        - port: The port
        - exception: The custom exception to raise
        """
        self.add_responses_for_host(
            host, port, {},
            connection_failure=ConnectionFailureConfig.custom_exception(exception)
        )

    def setup_badhost_failure(
        self,
        host: str,
        port: int,
        custom_got_key: PKey | None = None,
        custom_pkey: PKey | None = None
    ) -> None:
        """
        Set up a custom exception failure for a host.

        - host: The hostname to fail for
        - port: The port
        - exception: The custom exception to raise
        """
        self.add_responses_for_host(
            host, port, {},
            connection_failure=ConnectionFailureConfig.bad_host_exception(
                host, custom_got_key, custom_pkey
            )
        )
