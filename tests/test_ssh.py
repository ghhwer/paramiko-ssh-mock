import paramiko
from io import BytesIO
from src.paramiko_mock.mocked_env import ParamikoMockEnviron
from src.paramiko_mock.ssh_mock import (
    SSHClientMock, SSHCommandMock, SSHCommandFunctionMock, SSHResponseMock
)
from unittest.mock import patch


# Functions below are examples of what an application could look like
def example_function_1():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Some example of connection
    client.connect(
        'some_host',
        port=22,
        username='root',
        password='root',
        banner_timeout=10
    )
    stdin, stdout, stderr = client.exec_command('ls -l')
    return stdout.read()


def example_function_2():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Some example of connection
    client.connect(
        'some_host_2',
        port=4826,
        username='root',
        password='root',
        banner_timeout=10
    )
    stdin, stdout, stderr = client.exec_command('sudo docker ps')
    return stdout.read()


def example_function_3():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Some example of connection
    client.connect(
        'some_host_3',
        port=22,
        username='root',
        password='root',
        banner_timeout=10
    )
    stdin, stdout, stderr = client.exec_command('custom_command --param1 value1')
    return stdout.read()


def example_function_multiple_calls():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Some example of connection
    client.connect(
        'some_host',
        port=22,
        username='root',
        password='root',
        banner_timeout=10
    )
    client.exec_command('ls -l')
    client.exec_command('ls -al')


# Actual tests
# -- This ensures that the ParamikoMock is working as expected
def test_example_function_1():
    ParamikoMockEnviron().add_responses_for_host('some_host', 22, {
        'ls -l': SSHCommandMock('', 'ls output', '')
    }, 'root', 'root')
    with patch('paramiko.SSHClient', new=SSHClientMock):
        output = example_function_1()
        assert output == b'ls output'


def test_example_function_2():
    ParamikoMockEnviron().add_responses_for_host('some_host_2', 4826, {
        'sudo docker ps': SSHCommandMock('', 'docker-ps-output', '')
    }, 'root', 'root')
    # patch the paramiko.SSHClient with the mock
    with patch('paramiko.SSHClient', new=SSHClientMock):
        output = example_function_2()
        assert output == 'docker-ps-output'.encode()


def test_example_function_3():
    # We can also use a custom command processor
    def custom_command_processor(
        ssh_client_mock: SSHClientMock,
        command: str
    ):
        # Parse the command and do something with it
        if 'param1' in command and 'value1' in command:
            empty = ''.encode("utf-8")
            value = 'value1'.encode("utf-8")
            return BytesIO(empty), BytesIO(value), BytesIO(empty)

    # You can use a regexp expresion to match the command with the custom
    # processor
    ParamikoMockEnviron().add_responses_for_host('some_host_3', 22, {
        r're(custom_command .*)': SSHCommandFunctionMock(
            custom_command_processor
        )  # This is a regexp command
    }, 'root', 'root')
    # patch the paramiko.SSHClient with the mock
    with patch('paramiko.SSHClient', new=SSHClientMock):
        output = example_function_3()
        assert output == 'value1'.encode("utf-8")
    ParamikoMockEnviron().cleanup_environment()


def test_example_function_verify_commands_were_called():
    ParamikoMockEnviron().add_responses_for_host('some_host', 22, {
        're(ls.*)': SSHCommandMock('', 'ls output', '')
    }, 'root', 'root')
    with patch('paramiko.SSHClient', new=SSHClientMock):
        example_function_multiple_calls()
        # Use the assert commands to define the expected commands
        ParamikoMockEnviron().assert_command_executed_on_index(
            'some_host', 22, 'ls -l', 0
        )
        ParamikoMockEnviron().assert_command_executed_on_index(
            'some_host', 22, 'ls -al', 1
        )
        ParamikoMockEnviron().assert_command_was_executed(
            'some_host', 22, 'ls -l'
        )
        ParamikoMockEnviron().assert_command_was_executed(
            'some_host', 22, 'ls -al'
        )
        ParamikoMockEnviron().assert_command_was_not_executed(
            'some_host', 22, 'ls -alx'
        )
    ParamikoMockEnviron().cleanup_environment()


class MyCustomSSHResponse(SSHResponseMock):
    def __init__(self, *args, **kwargs):
        pass
        # You can initialize any custom attributes here

    def __call__(
        self,
        ssh_client_mock: SSHClientMock,
        command: str
    ) -> tuple[BytesIO, BytesIO, BytesIO]:
        # any custom logic here, you can use the command to determine the output
        # or the ssh_client_mock to get information about the connection
        command_output = ssh_client_mock.device.host + ' ' + command
        # Output should be in the form of (stdin, stdout, stderr)
        empty = "".encode()
        command_output = command_output.encode()
        return BytesIO(empty), BytesIO(command_output), BytesIO(empty)


def test_custom_class():
    ParamikoMockEnviron().add_responses_for_host('some_host', 22, {
        're(ls.*)': MyCustomSSHResponse()
    }, 'root', 'root')
    with patch('paramiko.SSHClient', new=SSHClientMock):
        output = example_function_1()
        assert output == 'some_host ls -l'.encode()
    ParamikoMockEnviron().cleanup_environment()
