import paramiko
import socket
from io import BytesIO
import pytest
from src.paramiko_mock.mocked_env import ParamikoMockEnviron
from src.paramiko_mock.ssh_mock import (
    SSHClientMock, SSHCommandMock, SSHCommandFunctionMock, SSHResponseMock
)
from src.paramiko_mock.mocked_env import ConnectionFailureConfig
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


# New tests for connection failure scenarios
def test_dns_failure():
    """
    Test that DNS resolution failure raises socket.gaierror.
    """
    # Set up DNS failure for a host
    ParamikoMockEnviron().setup_dns_failure('unreachable_host')

    def function_that_tries_to_connect():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('unreachable_host', port=22)
        stdin, stdout, stderr = client.exec_command('ls')
        return stdout.read()

    # Test that socket.gaierror is raised
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(socket.gaierror) as exc_info:
            function_that_tries_to_connect()

        # Verify the error message
        assert 'Name or service not known' in str(exc_info.value)
        assert exc_info.value.errno == -2

    ParamikoMockEnviron().cleanup_environment()


def test_dns_failure_with_custom_hostname():
    """
    Test that DNS resolution failure with custom hostname.
    """
    # Set up DNS failure with custom hostname
    ParamikoMockEnviron().setup_dns_failure('custom_host', hostname='custom.example.com')

    def function_that_tries_to_connect():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('custom_host', port=22)
        stdin, stdout, stderr = client.exec_command('ls')
        return stdout.read()

    # Test that socket.gaierror is raised with custom hostname
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(socket.gaierror) as exc_info:
            function_that_tries_to_connect()

        # Verify the custom hostname is in the error message
        assert 'custom.example.com' in str(exc_info.value)

    ParamikoMockEnviron().cleanup_environment()


def test_timeout_failure():
    """
    Test that connection timeout raises TimeoutError.
    """
    # Set up timeout failure for a host
    ParamikoMockEnviron().setup_timeout_failure('slow_host')

    def function_that_tries_to_connect():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('slow_host', port=22)
        stdin, stdout, stderr = client.exec_command('ls')
        return stdout.read()

    # Test that TimeoutError is raised
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(TimeoutError) as exc_info:
            function_that_tries_to_connect()

        # Verify the error message
        assert 'timed out' in str(exc_info.value)

    ParamikoMockEnviron().cleanup_environment()


def test_authentication_failure():
    """
    Test that authentication failure raises paramiko.ssh_exception.AuthenticationException.
    """
    # Set up authentication failure for a host
    ParamikoMockEnviron().setup_authentication_failure('auth_fail_host')

    def function_that_tries_to_connect():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('auth_fail_host', port=22, username='user', password='pass')
        stdin, stdout, stderr = client.exec_command('ls')
        return stdout.read()

    # Test that AuthenticationException is raised
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(paramiko.ssh_exception.AuthenticationException) as exc_info:
            function_that_tries_to_connect()

        # Verify the error message
        assert 'Authentication failed' in str(exc_info.value)

    ParamikoMockEnviron().cleanup_environment()


def test_connection_refused():
    """
    Test that connection refused raises ConnectionRefusedError.
    """
    # Set up connection refused for a host
    ParamikoMockEnviron().setup_connection_refused('refused_host')

    def function_that_tries_to_connect():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('refused_host', port=22)
        stdin, stdout, stderr = client.exec_command('ls')
        return stdout.read()

    # Test that ConnectionRefusedError is raised
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(ConnectionRefusedError) as exc_info:
            function_that_tries_to_connect()

        # Verify the error message
        assert 'Connection refused' in str(exc_info.value)

    ParamikoMockEnviron().cleanup_environment()


def test_custom_failure():
    """
    Test that custom exception can be configured.
    """
    # Set up custom failure for a host
    custom_exception = ValueError("Custom error message")
    ParamikoMockEnviron().setup_custom_failure('custom_fail_host', 22, custom_exception)

    def function_that_tries_to_connect():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('custom_fail_host', port=22)
        stdin, stdout, stderr = client.exec_command('ls')
        return stdout.read()

    # Test that the custom exception is raised
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(ValueError) as exc_info:
            function_that_tries_to_connect()

        # Verify the custom error message
        assert 'Custom error message' in str(exc_info.value)

    ParamikoMockEnviron().cleanup_environment()


def test_connection_failure_with_add_responses_for_host():
    """
    Test that connection failure can be set directly via add_responses_for_host.
    """
    # Set up failure using the direct method
    ParamikoMockEnviron().add_responses_for_host(
        'direct_fail_host', 22, {},
        connection_failure=ConnectionFailureConfig.timeout_failure()
    )

    def function_that_tries_to_connect():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('direct_fail_host', port=22)
        stdin, stdout, stderr = client.exec_command('ls')
        return stdout.read()

    # Test that TimeoutError is raised
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(TimeoutError):
            function_that_tries_to_connect()

    ParamikoMockEnviron().cleanup_environment()


def test_badhost_exception():
    """
    Test that connection failure can be set directly via add_responses_for_host.
    """
    # Set up failure using the direct method
    ParamikoMockEnviron().add_responses_for_host(
        'direct_fail_host', 22, {},
        connection_failure=ConnectionFailureConfig.timeout_failure()
    )

    def function_that_tries_to_connect():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('direct_fail_host', port=22)
        stdin, stdout, stderr = client.exec_command('ls')
        return stdout.read()

    # Test that TimeoutError is raised
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(TimeoutError):
            function_that_tries_to_connect()

    ParamikoMockEnviron().cleanup_environment()


def test_mixed_success_and_failure_hosts():
    """
    Test that some hosts can succeed while others fail.
    """
    # Set up a successful host
    ParamikoMockEnviron().add_responses_for_host('good_host', 22, {
        'ls': SSHCommandMock('', 'success', '')
    }, 'user', 'pass')

    # Set up a failing host
    ParamikoMockEnviron().setup_dns_failure('bad_host')

    def connect_to_good_host():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('good_host', port=22, username='user', password='pass')
        stdin, stdout, stderr = client.exec_command('ls')
        return stdout.read()

    def connect_to_bad_host():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('bad_host', port=22)
        stdin, stdout, stderr = client.exec_command('ls')
        return stdout.read()

    with patch('paramiko.SSHClient', new=SSHClientMock):
        # Good host should work
        output = connect_to_good_host()
        assert output == b'success'

        # Bad host should fail
        with pytest.raises(socket.gaierror):
            connect_to_bad_host()

    ParamikoMockEnviron().cleanup_environment()


def test_connection_failure_config_static_methods():
    """
    Test the ConnectionFailureConfig static methods directly.
    """
    # Test DNS failure
    dns_error = ConnectionFailureConfig.dns_failure('test.example.com')
    assert isinstance(dns_error, socket.gaierror)
    assert dns_error.errno == -2
    assert 'test.example.com' in str(dns_error)

    # Test timeout failure
    timeout_error = ConnectionFailureConfig.timeout_failure()
    assert isinstance(timeout_error, TimeoutError)
    assert 'timed out' in str(timeout_error)

    # Test authentication failure
    auth_error = ConnectionFailureConfig.authentication_failure()
    assert isinstance(auth_error, paramiko.ssh_exception.AuthenticationException)
    assert 'Authentication failed' in str(auth_error)

    # Test connection refused
    conn_refused = ConnectionFailureConfig.connection_refused()
    assert isinstance(conn_refused, ConnectionRefusedError)
    assert 'Connection refused' in str(conn_refused)

    # Test custom exception
    custom_error = ValueError("Test error")
    wrapped_error = ConnectionFailureConfig.custom_exception(custom_error)
    assert wrapped_error is custom_error


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


def test_failed_authentication_raises_bad_host_key_exception():
    """
    Test that BadHostKeyException is raised when authentication fails.
    This test creates a scenario where the provided credentials don't match
    the expected credentials, triggering the BadHostKeyException.
    """
    # Set up a host with specific credentials (correct: 'admin'/'secret123')
    ParamikoMockEnviron().add_responses_for_host('secure_host', 22, {
        'ls -l': SSHCommandMock('', 'file listing', '')
    }, 'admin', 'secret123')

    # Function that tries to connect with wrong credentials
    def function_with_wrong_credentials():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Try to connect with wrong credentials
        client.connect(
            'secure_host',
            port=22,
            username='wrong_user',  # Wrong username
            password='wrong_pass',  # Wrong password
            banner_timeout=10
        )
        stdin, stdout, stderr = client.exec_command('ls -l')
        return stdout.read()

    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(paramiko.AuthenticationException):
            function_with_wrong_credentials()
    ParamikoMockEnviron().cleanup_environment()


def test_failed_authentication_with_wrong_password():
    """
    Test that BadHostKeyException is raised when only the password is wrong.
    This test uses correct username but wrong password.
    """
    # Set up a host with specific credentials
    ParamikoMockEnviron().add_responses_for_host('auth_test_host', 2222, {
        'whoami': SSHCommandMock('', 'testuser', '')
    }, 'testuser', 'correct_password')

    # Function that tries to connect with wrong password only
    def function_with_wrong_password():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Correct username but wrong password
        client.connect(
            'auth_test_host',
            port=2222,
            username='testuser',        # Correct username
            password='wrong_password',  # Wrong password
            banner_timeout=10
        )
        stdin, stdout, stderr = client.exec_command('whoami')
        return stdout.read()

    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(paramiko.AuthenticationException):
            function_with_wrong_password()
    ParamikoMockEnviron().cleanup_environment()


def test_successful_authentication_after_failed_attempt():
    """
    Test that successful authentication works after a failed attempt on a different host.
    This ensures that failed authentication on one host doesn't affect other hosts.
    """
    # Set up two hosts: one with credentials, one without (open access)
    ParamikoMockEnviron().add_responses_for_host('protected_host', 22, {
        'ls': SSHCommandMock('', 'protected files', '')
    }, 'user', 'pass')

    ParamikoMockEnviron().add_responses_for_host('open_host', 22, {
        'ls': SSHCommandMock('', 'open files', '')
    })  # No credentials means open access

    def connect_to_protected_host():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('protected_host', port=22, username='user', password='pass')
        stdin, stdout, stderr = client.exec_command('ls')
        return stdout.read()

    def connect_to_open_host():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('open_host', port=22)
        stdin, stdout, stderr = client.exec_command('ls')
        return stdout.read()

    def fail_to_connect_to_protected_host():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('protected_host', port=22, username='wrong', password='wrong')
        stdin, stdout, stderr = client.exec_command('ls')
        return stdout.read()

    with patch('paramiko.SSHClient', new=SSHClientMock):
        # First, verify successful connection to protected host
        output1 = connect_to_protected_host()
        assert output1 == b'protected files'

        # Then, verify failed connection raises BadHostKeyException
        with pytest.raises(paramiko.AuthenticationException):
            fail_to_connect_to_protected_host()

        # Finally, verify open host still works (no credentials required)
        output2 = connect_to_open_host()
        assert output2 == b'open files'

    ParamikoMockEnviron().cleanup_environment()


def test_exit_status_functionality():
    """
    Test that the stderr object has channel with recv_exit_status() method.
    This verifies that the mock now supports exit status like the real paramiko library.
    """
    # Set up a host with a command that has a specific exit status
    ParamikoMockEnviron().add_responses_for_host('exit_status_host', 22, {
        'failing_command': SSHCommandMock('', 'output', 'error message', exit_status=1),
        'successful_command': SSHCommandMock('', 'success output', '', exit_status=0)
    }, 'user', 'pass')

    def execute_failing_command():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('exit_status_host', port=22, username='user', password='pass')
        stdin, stdout, stderr = client.exec_command('failing_command')
        return stdin, stdout, stderr

    def execute_successful_command():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('exit_status_host', port=22, username='user', password='pass')
        stdin, stdout, stderr = client.exec_command('successful_command')
        return stdin, stdout, stderr

    with patch('paramiko.SSHClient', new=SSHClientMock):
        # Test failing command
        stdin, stdout, stderr = execute_failing_command()

        # Verify stderr has channel attribute
        assert hasattr(stderr, 'channel'), "stderr should have a channel attribute"

        # Verify channel has recv_exit_status method
        assert hasattr(stderr.channel, 'recv_exit_status'), "channel should have recv_exit_status method"

        # Verify exit status is 1 for failing command
        exit_status = stderr.channel.recv_exit_status()
        assert exit_status == 1, f"Expected exit status 1, got {exit_status}"

        # Verify stderr still works as BytesIO
        stderr_content = stderr.read()
        assert stderr_content == b'error message', f"Expected 'error message', got {stderr_content}"

        # Test successful command
        stdin, stdout, stderr = execute_successful_command()
        exit_status = stderr.channel.recv_exit_status()
        assert exit_status == 0, f"Expected exit status 0, got {exit_status}"

    ParamikoMockEnviron().cleanup_environment()


def test_exit_status_with_custom_function():
    """
    Test that custom command functions can also return exit status.
    """
    def custom_command_processor(
        ssh_client_mock: SSHClientMock,
        command: str
    ):
        # Parse the command and determine exit status based on content
        if 'fail' in command:
            exit_status = 1
            stderr_content = 'Command failed'
        else:
            exit_status = 0
            stderr_content = ''

        empty = ''.encode("utf-8")
        stdout = 'custom output'.encode("utf-8")
        stderr_bytes = stderr_content.encode("utf-8")

        # Use StderrMock to provide exit status
        from src.paramiko_mock.stderr_mock import StderrMock
        stderr = StderrMock(stderr_bytes, exit_status)

        return BytesIO(empty), BytesIO(stdout), stderr

    # Set up a host with custom command processor
    ParamikoMockEnviron().add_responses_for_host('custom_host', 22, {
        r're(custom_command .*)': SSHCommandFunctionMock(
            custom_command_processor
        )
    }, 'user', 'pass')

    def execute_custom_command(command_str):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('custom_host', port=22, username='user', password='pass')
        stdin, stdout, stderr = client.exec_command(command_str)
        return stdin, stdout, stderr

    with patch('paramiko.SSHClient', new=SSHClientMock):
        # Test successful custom command
        stdin, stdout, stderr = execute_custom_command('custom_command --param value')
        exit_status = stderr.channel.recv_exit_status()
        assert exit_status == 0, f"Expected exit status 0, got {exit_status}"
        assert stdout.read() == b'custom output'

        # Test failing custom command
        stdin, stdout, stderr = execute_custom_command('custom_command --fail')
        exit_status = stderr.channel.recv_exit_status()
        assert exit_status == 1, f"Expected exit status 1, got {exit_status}"
        assert stderr.read() == b'Command failed'

    ParamikoMockEnviron().cleanup_environment()
