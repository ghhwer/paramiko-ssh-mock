# Usage

ParamikoMock aims to provide a simple way to mock the paramiko library for testing purposes. 
It is designed to be used in unit tests, where the actual connection to a remote host is needed.

When using ParamikoMock you will only need to interact with the following classes:

- `ParamikoMockEnviron` - Provides an interface to manage the mock environment.
- `LocalFileMock` - Provides a mock for local files.
- `SFTPFileMock` - Provides a mock for remote files.
- `SSHCommandMock` - Provides a definition for the output of a command.

The class `SSHClientMock` is used but only for patching the `paramiko.SSHClient` class.

## Setting up the environment

The `ParamikoMockEnviron` class is used to manage the mock environment.
You can read more about the methods available in the [API Reference](api#ParamikoMockEnviron).

### Using as as a simple patch

The simplest way to use ParamikoMock is to patch the `paramiko.SSHClient` class with the `SSHClientMock` class.
This will allow you to use the `paramiko.SSHClient` class as you normally would, but the actual connection will be mocked.

When using patching you need to ensure that the host is defined in the `ParamikoMockEnviron` class before calling your application code.

```python
from paramiko_mock import (
        SSHCommandMock, ParamikoMockEnviron,
        SSHClientMock
)
from unittest.mock import patch
import paramiko

def example_application_function_ssh():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Some example of connection
    client.connect('some_host',
                    port=22,
                    username='root',
                    password='root',
                    banner_timeout=10)
    stdin_1, stdout_1, stderr_1 = client.exec_command('ls -l')
    stdin_2, stdout_2, stderr_2 = client.exec_command('docker ps')
    return stdout_1.read(), stdout_2.read()

def test_example_application_function_ssh():
    # Add the responses for the host
    ParamikoMockEnviron().add_responses_for_host('myhost.example.ihf', 22, {
            're(ls.*)': SSHCommandMock('', 'ls output', ''),
            'docker ps': SSHCommandMock('', 'docker ps output', ''),
    }, 'root', 'root')

    with patch('paramiko.SSHClient', new=SSHClientMock):
        # Call your application code
        output_1, output_2 = example_application_function_ssh()
    
    # Do any assertions here    
    assert output_1 == b'ls output'
    assert output_2 == b'docker ps output'
    ParamikoMockEnviron().assert_command_was_executed('myhost.example.ihf', 22, 'ls -l')
    ParamikoMockEnviron().assert_command_was_executed('myhost.example.ihf', 22, 'docker ps')
    # Cleanup the environment
ParamikoMockEnviron().cleanup_environment()
```
`add_responses_for_host` supports regular expressions for the command to be executed. These will be matched against the command that is executed.

The `SSHCommandMock` class is used to define the output of the command.

`ParamikoMockEnviron().cleanup_environment()` is recommended to be called after each test to ensure that the environment is cleaned up.

## Testing Connection Failures

ParamikoMock now supports testing various connection failure scenarios, similar to how the `responses` library works for HTTP mocking. This allows you to test how your application handles different types of connection problems.

### Using Convenience Methods

The `ParamikoMockEnviron` class provides convenience methods for setting up common failure scenarios:

```python
from paramiko_mock import ParamikoMockEnviron
from unittest.mock import patch
import paramiko
import socket

def test_dns_failure():
    # Set up DNS resolution failure
    ParamikoMockEnviron().setup_dns_failure('unreachable_host')
    
    def connect_function():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('unreachable_host', port=22)
        return client
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(socket.gaierror) as exc_info:
            connect_function()
        assert 'Name or service not known' in str(exc_info.value)
    
    ParamikoMockEnviron().cleanup_environment()

def test_timeout_failure():
    # Set up connection timeout
    ParamikoMockEnviron().setup_timeout_failure('slow_host')
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(TimeoutError):
            connect_function()
    
    ParamikoMockEnviron().cleanup_environment()

def test_authentication_failure():
    # Set up authentication failure
    ParamikoMockEnviron().setup_authentication_failure('secure_host')
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(paramiko.ssh_exception.AuthenticationException):
            connect_function()
    
    ParamikoMockEnviron().cleanup_environment()

def test_connection_refused():
    # Set up connection refused
    ParamikoMockEnviron().setup_connection_refused('busy_host')
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(ConnectionRefusedError):
            connect_function()
    
    ParamikoMockEnviron().cleanup_environment()
```

### Using Custom Failures

You can also set up custom exceptions for specific scenarios:

```python
def test_custom_failure():
    # Set up a custom exception
    custom_exception = ValueError("Custom SSH error")
    ParamikoMockEnviron().setup_custom_failure('custom_host', 22, custom_exception)
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(ValueError) as exc_info:
            connect_function()
        assert 'Custom SSH error' in str(exc_info.value)
    
    ParamikoMockEnviron().cleanup_environment()
```

### Using ConnectionFailureConfig Directly

For more control, you can use the `ConnectionFailureConfig` class directly:

```python
from paramiko_mock.exceptions import ConnectionFailureConfig

def test_direct_failure_config():
    # Set up failure using the direct method
    ParamikoMockEnviron().add_responses_for_host(
        'direct_fail_host', 22, {},
        connection_failure=ConnectionFailureConfig.dns_failure('test.example.com')
    )
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(socket.gaierror) as exc_info:
            connect_function()
        assert 'test.example.com' in str(exc_info.value)
    
    ParamikoMockEnviron().cleanup_environment()
```

### Available Failure Types

The following failure types are available:

- **DNS Failure**: `socket.gaierror(-2, "Name or service not known: {hostname}")`
- **Timeout**: `TimeoutError("timed out")`
- **Authentication**: `paramiko.ssh_exception.AuthenticationException("Authentication failed")`
- **Connection Refused**: `ConnectionRefusedError("Connection refused")`
- **Custom**: Any exception you provide

### Mixing Success and Failure Scenarios

You can set up different hosts with different behaviors in the same test:

```python
def test_mixed_scenarios():
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
        return client
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        # Good host should work
        output = connect_to_good_host()
        assert output == b'success'
        
        # Bad host should fail
        with pytest.raises(socket.gaierror):
            connect_to_bad_host()
    
    ParamikoMockEnviron().cleanup_environment()
```

### Using it as a extended class of `unittest.TestCase`

You can also setup a test case that extends `unittest.TestCase` and uses the `ParamikoMock` class to manage the mock environment.

```python
import unittest
import pytest
from unittest.mock import patch
from src.paramiko_mock import (SSHClientMock, ParamikoMockEnviron, SSHCommandMock)
import paramiko

def my_application_code():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Some example of connection
    client.connect('some_host',
                    port=22,
                    username='root',
                    password='root',
                    banner_timeout=10)
    stdin, stdout, stderr = client.exec_command('ls -l')
    return stdout.read()

class ParamikoMockTestCase(unittest.TestCase):
    @classmethod
    @pytest.fixture(scope='class', autouse=True)
    def setup_and_teardown(cls):
        # Setup your environment
        ParamikoMockEnviron().add_responses_for_host('some_host', 22, {
            'ls -l': SSHCommandMock('', 'ls -l output', ''),
        }, 'root', 'root')
        with patch('paramiko.SSHClient', new=SSHClientMock): 
            yield
        # Teardown your environment
        ParamikoMockEnviron().cleanup_environment()
    
    def test_paramiko_mock(self):
        output = my_application_code()
        assert output == 'ls -l output'
```

Extending `unittest.TestCase` can help you to manage the environment for your tests. 
The `setup_and_teardown` method is used to setup and teardown the environment for your tests.

## Setting up the environment for SSH operations

The `ParamikoMockEnviron` class can be used to manage the environment for SSH operations.
You can either use `SSHCommandMock` to define the output of a command or define a custom class that implements the abstract class: `SSHResponseMock`.

Use the `SSHCommandMock` class to define the output of a command:
```python
from paramiko_mock import ParamikoMockEnviron, SSHCommandMock
# ...
# Setup the environment for SSH operations
ParamikoMockEnviron().add_responses_for_host('myhost.example.ihf', 22, {
        're(ls.*)': SSHCommandMock('', 'ls output', ''),
        'docker ps': SSHCommandMock('', 'docker ps output', ''),
}, 'root', 'root')
# ...
```

Implementing a custom class that extends `SSHResponseMock`:
```python
from paramiko_mock import SSHResponseMock, ParamikoMockEnviron, SSHClientMock
from io import BytesIO

# ...
# Define a custom class that extends SSHResponseMock
class MyCustomSSHResponse(SSHResponseMock):
    def __init__(self, *args, **kwargs):
        pass
        # You can initialize any custom attributes here
    
    def __call__(self, ssh_client_mock: SSHClientMock, command:str) -> tuple[BytesIO, BytesIO, BytesIO]:
        # any custom logic here, you can use the command to determine the output 
        # or the ssh_client_mock to get information about the connection
        command_output = ssh_client_mock.device.host + ' ' + command
        # Output should be in the form of (stdin, stdout, stderr)
        return BytesIO("".encode()), BytesIO(command_output.encode()), BytesIO("".encode())

# Setup the environment for SSH operations
ParamikoMockEnviron().add_responses_for_host('myhost.example.ihf', 22, {
        're(ls.*)': MyCustomSSHResponse(), # Register the custom class
}, 'root', 'root')
# ...
```

## Setting up the environment for SFTP operations

The `ParamikoMockEnviron` class can also be used to manage the environment for SFTP operations.
You should use the `LocalFileMock` class to define the local files and the `SFTPFileMock` class to define the remote files.

```python
# ...
# Setup the environment for SFTP operations
ParamikoMockEnviron().add_responses_for_host('myhost.example.ihf', 22, {}, 'root', 'root')

# Local files can be mocked using the LocalFileMock class
mock_local_file = LocalFileMock()
mock_local_file.file_content = 'Local file content'
ParamikoMockEnviron().add_local_file('/local/path/to/file_a.txt', mock_local_file)

# Remote files can be mocked using the SFTPFileMock class
mock_remote_file = SFTPFileMock()
mock_remote_file.file_content = 'Remote file content'
ParamikoMockEnviron().add_mock_file_for_host('myhost.example.ihf', 22, '/remote/path/to/file_b.txt', mock_remote_file)
# ...
```

`ParamikoMockEnviron` also provides interfaces for getting the local and remote files:
```python
# ...
# Get the local file
file_on_local = ParamikoMockEnviron().get_local_file('/local/path/to/file_a.txt')
assert file_on_local.file_content == 'Local file content'

# Get the remote file
file_on_remote = ParamikoMockEnviron().get_mock_file_for_host('myhost.example.ihf', 22, '/remote/path/to/file_b.txt')
assert file_on_remote.file_content == 'Remote file content'
# ...
```

## Conclusion

ParamikoMock provides a simple way to mock the paramiko library for testing purposes.

It does not provide a full implementation of the paramiko library, but it is designed to be used in unit tests where the actual connection to a remote host is needed.
Contributions are welcome, and you can see how to contribute in the [Contributing Guide](contributing).
