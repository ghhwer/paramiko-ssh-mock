# Basic SSH Operations

ParamikoMock provides a simple way to mock SSH commands for testing purposes. This section covers the basic SSH operations and how to set up mock responses.

## Setting up the environment

The `ParamikoMockEnviron` class is used to manage the mock environment.
You can read more about the methods available in the [API Reference](/autoapi/paramiko_mock/).

### Using as a simple patch

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
    client.connect(
        'some_host',
        port=22,
        username='root',
        password='root',
        banner_timeout=10
    )
    stdin_1, stdout_1, stderr_1 = client.exec_command('ls -l')
    stdin_2, stdout_2, stderr_2 = client.exec_command('docker ps')
    return stdout_1.read(), stdout_2.read()

def test_example_application_function_ssh():
    # Add the responses for the host
    ParamikoMockEnviron().add_responses_for_host(
        host='myhost.example.ihf', 
        port=22, 
        responses={
            're(ls.*)': SSHCommandMock('', 'ls output', ''),
            'docker ps': SSHCommandMock('', 'docker ps output', ''),
        }, 
        username='root', 
        password='root'
    )

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

## Setting up the environment for SSH operations

The `ParamikoMockEnviron` class can be used to manage the environment for SSH operations.
You can either use `SSHCommandMock` to define the output of a command or define a custom class that implements the abstract class: `SSHResponseMock`.

### Using SSHCommandMock

Use the `SSHCommandMock` class to define the output of a command:

```python
from paramiko_mock import ParamikoMockEnviron, SSHCommandMock
# ...
# Setup the environment for SSH operations
ParamikoMockEnviron().add_responses_for_host(
        host='myhost.example.ihf', 
        port=22, 
        responses={
                're(ls.*)': SSHCommandMock('', 'ls output', ''),
                'docker ps': SSHCommandMock('', 'docker ps output', ''),
        }, 
        username='root', 
        password='root'
)
# ...
```

### Using Custom SSH Response Classes

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
ParamikoMockEnviron().add_responses_for_host(
        host='myhost.example.ihf', 
        port=22, 
        responses={
                're(ls.*)': MyCustomSSHResponse(), # Register the custom class
        }, 
        username='root', 
        password='root'
)
# ...
```

## Complete Example

Here is a complete example demonstrating basic SSH operations:

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
        client.connect(
            'myhost.example.ihf', 
            port=22, 
            username='root', 
            password='root', 
            banner_timeout=10
        )
        stdin, stdout, stderr = client.exec_command('ls -l')
        output_1 = stdout.read()
        stdin, stdout, stderr = client.exec_command('docker ps')
        output_2 = stdout.read()
        return output_1, output_2

def test_example_application_function_ssh():
        ParamikoMockEnviron().add_responses_for_host(
                host='myhost.example.ihf', 
                port=22, 
                responses={
                        're(ls.*)': SSHCommandMock('', 'ls output', ''),
                        'docker ps': SSHCommandMock('', 'docker ps output', ''),
                }, 
                username='root', 
                password='root'
        )

        with patch('paramiko.SSHClient', new=SSHClientMock):
                output_1, output_2 = example_application_function_ssh()
                assert output_1 == b'ls output'
                assert output_2 == b'docker ps output'
                # Custom enviroment asserts
                ParamikoMockEnviron().assert_command_was_executed('myhost.example.ihf', 22, 'ls -l')
                ParamikoMockEnviron().assert_command_was_executed('myhost.example.ihf', 22, 'docker ps')
        
        ParamikoMockEnviron().cleanup_environment()
```