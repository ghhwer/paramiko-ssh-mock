from abc import abstractmethod, ABC
from io import StringIO
import re
from paramiko.ssh_exception import BadHostKeyException, NoValidConnectionsError
from .sftp_mock import SFTPClientMock
from .mocked_env import ParamikoMockEnviron

class SSHClientMock():
    """
    The SSHClientMock is a class that mocks the paramiko.SSHClient class.
    This class is intended to be patched in place of the paramiko.SSHClient class.
    """
    def __init__(self, *args, **kwds):
        self.device = None
        self.sftp_client_mock = None
    
    def set_missing_host_key_policy(self, policy):
        pass

    def open_sftp(self):
        if self.device is None:
            raise NoValidConnectionsError('No valid connection')
        if self.sftp_client_mock is None:
            # Create a new SFTPClientMock instance with the filesystem for the selected host
            self.sftp_client_mock = SFTPClientMock(
                self.device.filesystem,
                self.device.local_filesystem
            )
        return self.sftp_client_mock
    
    def set_log_channel(self, log_channel):
        pass
    
    def get_host_keys(self):
        pass
    
    def save_host_keys(self, filename):
        pass
    
    def load_host_keys(self, filename):
        pass
    
    def load_system_host_keys(self, filename=None):
        pass
    
    def connect(
        self, hostname, 
        port=22, username=None, password=None, 
        **kwargs
    ):
        self.selected_host = f'{hostname}:{port}'
        self.device = ParamikoMockEnviron()._get_remote_device(self.selected_host)
        if self.device.authenticate(username, password) is False:
            raise BadHostKeyException(hostname, None, 'Invalid credentials')
        self.last_connect_kwargs = kwargs
        self.device.clear()
    
    def exec_command(self, command, bufsize=-1, timeout=None, get_pty=False, environment=None):
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
    
    def invoke_shell(self, term='vt100', width=80, height=24, width_pixels=0, height_pixels=0, environment=None):
        pass
    
    def close(self):
        self.device = None


class SSHResponseMock(ABC):
    """
    The SSHResponseMock is a generic class that represents a response for a command.
    This can be used to create custom responses for commands that would invoke a callback.
    """
    @abstractmethod
    def __call__(self, ssh_client_mock: SSHClientMock, command:str) -> tuple[StringIO, StringIO, StringIO]:
        """
        A method that should be implemented by the subclasses.
        This method is called when the command is executed
        
        - ssh_client_mock: The SSHClientMock instance that is executing the command.
        - command: The command that is being executed.
        
        Returns: A tuple of StringIO objects.
        """
        pass

class SSHCommandMock(SSHResponseMock):
    """
    SSHCommandMock is a class that represents a response for a command.
    It's constructed with the stdin, stdout, and stderr that the command will return.
    
    When called the instance of this class will return a tuple of StringIO objects.
    
    - stdin: The stdin of the command.
    - stdout: The stdout of the command.
    - stderr: The stderr of the command.
    """
    def __init__(self, stdin, stdout, stderr):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    def __call__(self, ssh_client_mock: SSHClientMock, command:str) -> tuple[StringIO, StringIO, StringIO]:
        return StringIO(self.stdin), StringIO(self.stdout), StringIO(self.stderr)

    def append_to_stdout(self, new_stdout):
        self.stdout += new_stdout
    
    def remove_line_containing(self, line):
        self.stdout = '\n'.join([x for x in self.stdout.split('\n') if line not in x])

class SSHCommandFunctionMock(SSHResponseMock):
    def __init__(self, callback):
        self.callback = callback
    
    def __call__(self, ssh_client_mock: SSHClientMock, command:str) -> tuple[StringIO, StringIO, StringIO]:
        return self.callback(ssh_client_mock, command)
