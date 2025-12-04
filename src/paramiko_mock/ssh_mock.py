from abc import abstractmethod, ABC
from io import BytesIO
import re
from typing import Any, Callable, Union
from paramiko.ssh_exception import NoValidConnectionsError, AuthenticationException
from .sftp_mock import SFTPClientMock
from .mocked_env import ParamikoMockEnviron, MockRemoteDevice


class SSHClientMock():
    """
    The SSHClientMock is a class that mocks the paramiko.SSHClient class.
    This class is intended to be patched in place of the paramiko.SSHClient class.
    """

    def __init__(self, *args: Any, **kwds: Any) -> None:
        self.device: Union[MockRemoteDevice, None] = None
        self.sftp_client_mock: Union[SFTPClientMock, None] = None

    def set_missing_host_key_policy(self, policy: Any) -> None:
        pass

    def open_sftp(self) -> SFTPClientMock:
        if self.device is None:
            raise NoValidConnectionsError('No valid connection')
        if self.sftp_client_mock is None:
            # Create a new SFTPClientMock instance with the filesystem for the
            # selected host
            self.sftp_client_mock = SFTPClientMock(
                self.device.filesystem,
                self.device.local_filesystem
            )
        return self.sftp_client_mock

    def set_log_channel(self, log_channel: str) -> None:
        pass

    def get_host_keys(self) -> None:
        pass

    def save_host_keys(self, filename: str) -> None:
        pass

    def load_host_keys(self, filename: str) -> None:
        pass

    def load_system_host_keys(self, filename: Union[str, None] = None) -> None:
        pass

    def connect(
        self,
        hostname: str,
        port: int = 22,
        username: Union[str, None] = None,
        password: Union[str, None] = None,
        **kwargs: Any
    ) -> None:
        self.selected_host = f'{hostname}:{port}'
        self.device = ParamikoMockEnviron().get_remote_device(
            self.selected_host
        )

        # Check for connection failure configuration
        if self.device.connection_failure is not None:
            raise self.device.connection_failure

        # Check authentication
        if self.device.authenticate(username, password) is False:
            raise AuthenticationException()

        self.last_connect_kwargs = kwargs
        self.device.clear()

    def exec_command(
        self,
        command: str,
        bufsize: int = -1,
        timeout: Union[int, None] = None,
        get_pty: bool = False,
        environment: Union[dict[str, str], None] = None
    ) -> tuple[BytesIO, BytesIO, BytesIO]:
        if self.selected_host is None:
            raise NoValidConnectionsError('No valid connections')
        self.device.add_command_to_history(command)
        response = self.device.responses.get(command)
        if response is None:
            # check if there is a command that can be used as regexp
            for command_key in self.device.responses:
                if command_key.startswith('re(') and command_key.endswith(')'):
                    regexp_exp = command_key[3:-1]
                    if re.match(regexp_exp, command):
                        response = self.device.responses[command_key]
                        break
            if response is None:
                raise NotImplementedError('No valid response for this command')
        return response(self, command)

    def invoke_shell(
        self,
        term: str = 'vt100',
        width: int = 80,
        height: int = 24,
        width_pixels: int = 0,
        height_pixels: int = 0,
        environment: Union[dict[str, str], None] = None
    ) -> None:
        pass

    def close(self) -> None:
        self.device = None


class SSHResponseMock(ABC):
    """
    The SSHResponseMock is a generic class that represents a response for a
    command. This can be used to create custom responses for commands that would
    invoke a callback.
    """

    @abstractmethod
    def __call__(
        self,
        ssh_client_mock: SSHClientMock,
        command: str
    ) -> tuple[BytesIO, BytesIO, BytesIO]:
        """
        A method that should be implemented by the subclasses.
        This method is called when the command is executed

        - ssh_client_mock: The SSHClientMock instance that is executing the
          command.
        - command: The command that is being executed.

        Returns: A tuple of BytesIO objects.
        """
        pass


class SSHCommandMock(SSHResponseMock):
    """
    SSHCommandMock is a class that represents a response for a command.
    It's constructed with the stdin, stdout, and stderr that the command will
    return.

    When called the instance of this class will return a tuple of BytesIO
    objects.

    - stdin: The stdin of the command.
    - stdout: The stdout of the command.
    - stderr: The stderr of the command.
    """

    def __init__(
        self,
        stdin: Union[str, BytesIO],
        stdout: Union[str, BytesIO],
        stderr: Union[str, BytesIO],
        str_encoding="utf-8"
    ) -> None:
        if isinstance(stdin, str):
            stdin = BytesIO(stdin.encode(str_encoding))
        if isinstance(stdout, str):
            stdout = BytesIO(stdout.encode(str_encoding))
        if isinstance(stderr, str):
            stderr = BytesIO(stderr.encode(str_encoding))
        self.stdin: str = stdin
        self.stdout: str = stdout
        self.stderr: str = stderr

    def __call__(
        self,
        ssh_client_mock: SSHClientMock,
        command: str
    ) -> tuple[BytesIO, BytesIO, BytesIO]:
        return self.stdin, self.stdout, self.stderr

    def append_to_stdout(self, new_stdout: str) -> None:
        self.stdout += new_stdout

    def remove_line_containing(self, line: str) -> None:
        self.stdout = '\n'.join(
            [x for x in self.stdout.split('\n') if line not in x]
        )


class SSHCommandFunctionMock(SSHResponseMock):
    def __init__(
        self,
        callback: Callable[[SSHClientMock, str], tuple[BytesIO, BytesIO, BytesIO]]
    ) -> None:
        self.callback: Callable[[SSHClientMock, str], tuple[BytesIO, BytesIO, BytesIO]] = callback

    def __call__(
        self,
        ssh_client_mock: SSHClientMock,
        command: str
    ) -> tuple[BytesIO, BytesIO, BytesIO]:
        return self.callback(ssh_client_mock, command)
