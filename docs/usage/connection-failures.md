# Connection Failures Testing

ParamikoMock now supports testing various connection failure scenarios, similar to how the `responses` library works for HTTP mocking. This allows you to test how your application handles different types of connection problems.

## Using Convenience Methods

The `ParamikoMockEnviron` class provides convenience methods for setting up common failure scenarios:

### DNS Failure

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
```

### Timeout Failure

```python
def test_timeout_failure():
    # Set up connection timeout
    ParamikoMockEnviron().setup_timeout_failure('slow_host')
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(TimeoutError):
            connect_function()
    
    ParamikoMockEnviron().cleanup_environment()
```

### Authentication Failure

```python
def test_authentication_failure():
    # Set up authentication failure
    ParamikoMockEnviron().setup_authentication_failure('secure_host')
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(paramiko.ssh_exception.AuthenticationException):
            connect_function()
    
    ParamikoMockEnviron().cleanup_environment()
```

### Connection Refused

```python
def test_connection_refused():
    # Set up connection refused
    ParamikoMockEnviron().setup_connection_refused('busy_host')
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(ConnectionRefusedError):
            connect_function()
    
    ParamikoMockEnviron().cleanup_environment()
```

### Bad Host Key

```python
def test_bad_host_key():
    # Set up bad host key failure
    ParamikoMockEnviron().setup_badhost_failure('suspicious_host')
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(paramiko.BadHostKeyException):
            connect_function()
    
    ParamikoMockEnviron().cleanup_environment()
```

### Bad Host Key with Custom Keys

```python
def test_bad_host_key_custom():
    # Set up bad host key failure with custom keys
    from paramiko.pkey import PKey
    from paramiko.message import Message
    
    custom_got_key = PKey(msg=Message("CustomGotKey".encode()), data="CustomGotKeyData")
    custom_pkey = PKey(msg=Message("CustomExpectedKey".encode()), data="CustomExpectedKeyData")
    
    ParamikoMockEnviron().setup_badhost_failure(
        'suspicious_host', 
        custom_got_key=custom_got_key, 
        custom_pkey=custom_pkey
    )
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        with pytest.raises(paramiko.BadHostKeyException) as exc_info:
            connect_function()
        
        # You can inspect the exception details
        exception = exc_info.value
        assert exception.hostname == 'suspicious_host'
        assert exception.got_key == custom_got_key
        assert exception.pkey == custom_pkey
    
    ParamikoMockEnviron().cleanup_environment()
```

## Using Custom Failures

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

## Using ConnectionFailureConfig Directly

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

## Available Failure Types

The following failure types are available:

- **DNS Failure**: `socket.gaierror(-2, "Name or service not known: {hostname}")`
- **Timeout**: `TimeoutError("timed out")`
- **Authentication**: `paramiko.ssh_exception.AuthenticationException("Authentication failed")`
- **Connection Refused**: `ConnectionRefusedError("Connection refused")`
- **Bad Host Key**: `paramiko.BadHostKeyException(hostname, got_key, pkey)`
- **Custom**: Any exception you provide

## Mixing Success and Failure Scenarios

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

## Complete Example

Here's a comprehensive example showing various connection failure scenarios:

```python
import pytest
from paramiko_mock import ParamikoMockEnviron, SSHClientMock, SSHCommandMock
from unittest.mock import patch
import paramiko
import socket

class TestConnectionFailures:
    def test_dns_resolution_failure(self):
        """Test DNS resolution failure scenario"""
        ParamikoMockEnviron().setup_dns_failure('nonexistent.example.com')
        
        with patch('paramiko.SSHClient', new=SSHClientMock):
            with pytest.raises(socket.gaierror) as exc_info:
                client = paramiko.SSHClient()
                client.connect('nonexistent.example.com', port=22)
            
            assert 'Name or service not known' in str(exc_info.value)
        
        ParamikoMockEnviron().cleanup_environment()
    
    def test_connection_timeout(self):
        """Test connection timeout scenario"""
        ParamikoMockEnviron().setup_timeout_failure('slow-server.example.com')
        
        with patch('paramiko.SSHClient', new=SSHClientMock):
            with pytest.raises(TimeoutError):
                client = paramiko.SSHClient()
                client.connect('slow-server.example.com', port=22)
        
        ParamikoMockEnviron().cleanup_environment()
    
    def test_authentication_failure(self):
        """Test authentication failure scenario"""
        ParamikoMockEnviron().setup_authentication_failure('secure-server.example.com')
        
        with patch('paramiko.SSHClient', new=SSHClientMock):
            with pytest.raises(paramiko.ssh_exception.AuthenticationException):
                client = paramiko.SSHClient()
                client.connect('secure-server.example.com', port=22, username='user', password='pass')
        
        ParamikoMockEnviron().cleanup_environment()
    
    def test_connection_refused(self):
        """Test connection refused scenario"""
        ParamikoMockEnviron().setup_connection_refused('busy-server.example.com')
        
        with patch('paramiko.SSHClient', new=SSHClientMock):
            with pytest.raises(ConnectionRefusedError):
                client = paramiko.SSHClient()
                client.connect('busy-server.example.com', port=22)
        
        ParamikoMockEnviron().cleanup_environment()
    
    def test_bad_host_key(self):
        """Test bad host key scenario"""
        ParamikoMockEnviron().setup_badhost_failure('suspicious-server.example.com')
        
        with patch('paramiko.SSHClient', new=SSHClientMock):
            with pytest.raises(paramiko.BadHostKeyException):
                client = paramiko.SSHClient()
                client.connect('suspicious-server.example.com', port=22)
        
        ParamikoMockEnviron().cleanup_environment()
    
    def test_custom_exception(self):
        """Test custom exception scenario"""
        custom_error = RuntimeError("Custom network error")
        ParamikoMockEnviron().setup_custom_failure('custom-error.example.com', 22, custom_error)
        
        with patch('paramiko.SSHClient', new=SSHClientMock):
            with pytest.raises(RuntimeError) as exc_info:
                client = paramiko.SSHClient()
                client.connect('custom-error.example.com', port=22)
            
            assert 'Custom network error' in str(exc_info.value)
        
        ParamikoMockEnviron().cleanup_environment()
    
    def test_mixed_success_and_failure(self):
        """Test mixing successful and failing connections in the same test"""
        # Set up successful host
        ParamikoMockEnviron().add_responses_for_host('working-host.example.com', 22, {
            'uptime': SSHCommandMock('', 'Server is up', '')
        }, 'user', 'pass')
        
        # Set up failing host
        ParamikoMockEnviron().setup_connection_refused('failing-host.example.com')
        
        def execute_on_working_host():
            client = paramiko.SSHClient()
            client.connect('working-host.example.com', port=22, username='user', password='pass')
            stdin, stdout, stderr = client.exec_command('uptime')
            return stdout.read()
        
        def connect_to_failing_host():
            client = paramiko.SSHClient()
            client.connect('failing-host.example.com', port=22)
            return client
        
        with patch('paramiko.SSHClient', new=SSHClientMock):
            # Working host should succeed
            result = execute_on_working_host()
            assert result == b'Server is up'
            
            # Failing host should raise exception
            with pytest.raises(ConnectionRefusedError):
                connect_to_failing_host()
        
        ParamikoMockEnviron().cleanup_environment()
```

This comprehensive testing approach allows you to verify that your application handles various network failure scenarios gracefully and appropriately.
