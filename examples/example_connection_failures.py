import paramiko
import socket
from unittest.mock import patch
from paramiko_mock import (
    SSHClientMock, 
    ParamikoMockEnviron, 
    SSHCommandMock
)


def connect_to_host(hostname, username='user', password='pass'):
    """Example function that connects to an SSH host."""
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port=22, username=username, password=password)
        stdin, stdout, stderr = client.exec_command('echo "Hello World"')
        return stdout.read().decode().strip()
    finally:
        client.close()


def test_dns_failure():
    """Test DNS resolution failure."""
    print("Testing DNS failure...")
    
    # Set up DNS failure
    ParamikoMockEnviron().setup_dns_failure('unreachable.example.com')
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        try:
            result = connect_to_host('unreachable.example.com')
            print(f"Unexpected success: {result}")
        except socket.gaierror as e:
            print(f"[OK] DNS failure caught: {e}")
        finally:
            ParamikoMockEnviron().cleanup_environment()


def test_timeout_failure():
    """Test connection timeout."""
    print("\nTesting timeout failure...")
    
    # Set up timeout failure
    ParamikoMockEnviron().setup_timeout_failure('slow.example.com')
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        try:
            result = connect_to_host('slow.example.com')
            print(f"Unexpected success: {result}")
        except TimeoutError as e:
            print(f"[OK] Timeout caught: {e}")
        finally:
            ParamikoMockEnviron().cleanup_environment()


def test_authentication_failure():
    """Test authentication failure."""
    print("\nTesting authentication failure...")
    
    # Set up authentication failure
    ParamikoMockEnviron().setup_authentication_failure('secure.example.com')
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        try:
            result = connect_to_host('secure.example.com')
            print(f"Unexpected success: {result}")
        except paramiko.ssh_exception.AuthenticationException as e:
            print(f"[OK] Authentication failure caught: {e}")
        finally:
            ParamikoMockEnviron().cleanup_environment()


def test_connection_refused():
    """Test connection refused."""
    print("\nTesting connection refused...")
    
    # Set up connection refused
    ParamikoMockEnviron().setup_connection_refused('busy.example.com')
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        try:
            result = connect_to_host('busy.example.com')
            print(f"Unexpected success: {result}")
        except ConnectionRefusedError as e:
            print(f"[OK] Connection refused caught: {e}")
        finally:
            ParamikoMockEnviron().cleanup_environment()


def test_custom_failure():
    """Test custom exception."""
    print("\nTesting custom failure...")
    
    # Set up custom failure
    custom_error = RuntimeError("Custom SSH error occurred")
    ParamikoMockEnviron().setup_custom_failure('custom.example.com', 22, custom_error)
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        try:
            result = connect_to_host('custom.example.com')
            print(f"Unexpected success: {result}")
        except RuntimeError as e:
            print(f"[OK] Custom error caught: {e}")
        finally:
            ParamikoMockEnviron().cleanup_environment()


def test_successful_connection():
    """Test successful connection for comparison."""
    print("\nTesting successful connection...")
    
    # Set up successful connection
    ParamikoMockEnviron().add_responses_for_host('good.example.com', 22, {
        'echo "Hello World"': SSHCommandMock('', 'Hello World', '')
    }, 'user', 'pass')
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        try:
            result = connect_to_host('good.example.com')
            print(f"[OK] Success: {result}")
        except Exception as e:
            print(f"Unexpected failure: {e}")
        finally:
            ParamikoMockEnviron().cleanup_environment()


def test_mixed_scenarios():
    """Test mixing successful and failing hosts."""
    print("\nTesting mixed scenarios...")
    
    # Set up one successful host and one failing host
    ParamikoMockEnviron().add_responses_for_host('working.example.com', 22, {
        'echo "Hello World"': SSHCommandMock('', 'Hello World', '')
    }, 'user', 'pass')
    
    ParamikoMockEnviron().setup_dns_failure('broken.example.com')
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        # Working host should succeed
        try:
            result = connect_to_host('working.example.com')
            print(f"[OK] Working host: {result}")
        except Exception as e:
            print(f"[FAIL] Working host failed: {e}")
        
        # Broken host should fail
        try:
            result = connect_to_host('broken.example.com')
            print(f"[FAIL] Broken host unexpectedly succeeded: {result}")
        except socket.gaierror as e:
            print(f"[OK] Broken host correctly failed: {e}")
        
        ParamikoMockEnviron().cleanup_environment()


if __name__ == '__main__':
    print("ParamikoMock Connection Failure Examples")
    print("=" * 50)
    
    test_dns_failure()
    test_timeout_failure()
    test_authentication_failure()
    test_connection_refused()
    test_custom_failure()
    test_successful_connection()
    test_mixed_scenarios()
    
    print("\n" + "=" * 50)
    print("All examples completed!")
