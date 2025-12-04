# Exit Status Testing

ParamikoMock supports mocking exit status for SSH commands, allowing you to test how your application handles different command execution outcomes. This is particularly useful for testing error handling and conditional logic based on command success or failure.

## Basic Exit Status Usage

The `SSHCommandMock` class accepts an `exit_status` parameter to specify the exit status code for a command:

```python
from paramiko_mock import (
    SSHCommandMock, ParamikoMockEnviron,
    SSHClientMock
)
from unittest.mock import patch
import paramiko

def test_exit_status_functionality():
    # Set up mock responses with different exit statuses
    responses_map = {
        'ls -l': SSHCommandMock('', 'file1.txt\nfile2.txt', '', exit_status=0),
        'cat missing_file.txt': SSHCommandMock('', '', 'cat: missing_file.txt: No such file or directory', exit_status=1),
        'docker ps': SSHCommandMock('', '', 'Error: permission denied', exit_status=126)
    },
    ParamikoMockEnviron().add_responses_for_host(
        host='test_host', 
        port=22, 
        responses=responses_map, 
        username='user', 
        password='pass'
    )

    def application_code():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('test_host', port=22, username='user', password='pass')
        
        # Test successful command
        stdin, stdout, stderr = client.exec_command('ls -l')
        exit_status = stderr.channel.recv_exit_status()
        
        if exit_status == 0:
            print(f"Success: {stdout.read().decode()}")
        else:
            print(f"Failed: {stderr.read().decode()}")
        
        # Test failed command
        stdin, stdout, stderr = client.exec_command('cat missing_file.txt')
        exit_status = stderr.channel.recv_exit_status()
        
        if exit_status == 0:
            print(f"Success: {stdout.read().decode()}")
        else:
            print(f"Failed (status {exit_status}): {stderr.read().decode()}")
        
        return exit_status

    with patch('paramiko.SSHClient', new=SSHClientMock):
        result = application_code()
        # Verify the commands were executed
        ParamikoMockEnviron().assert_command_was_executed('test_host', 22, 'ls -l')
        ParamikoMockEnviron().assert_command_was_executed('test_host', 22, 'cat missing_file.txt')
    
    ParamikoMockEnviron().cleanup_environment()
```

## Common Exit Status Patterns

Here are some common exit status patterns you might want to test:

```python
def test_common_exit_status_patterns():
    ParamikoMockEnviron().add_responses_for_host('server', 22, {
        # Success (0)
        'success_command': SSHCommandMock('', 'Operation completed successfully', '', exit_status=0),
        
        # General error (1)
        'general_error': SSHCommandMock('', '', 'General error occurred', exit_status=1),
        
        # Command not found (127)
        'invalid_command': SSHCommandMock('', '', 'command not found', exit_status=127),
        
        # Permission denied (126)
        'permission_error': SSHCommandMock('', '', 'Permission denied', exit_status=126),
        
        # Custom exit status
        'custom_status': SSHCommandMock('', '', 'Custom application error', exit_status=42)
    }, 'user', 'pass')

    with patch('paramiko.SSHClient', new=SSHClientMock):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('server', port=22, username='user', password='pass')
        
        commands = ['success_command', 'general_error', 'invalid_command', 'permission_error', 'custom_status']
        
        for cmd in commands:
            stdin, stdout, stderr = client.exec_command(cmd)
            exit_status = stderr.channel.recv_exit_status()
            print(f"Command '{cmd}' exited with status: {exit_status}")
    
    ParamikoMockEnviron().cleanup_environment()
```

## Testing Error Handling Logic

Exit status mocking is particularly useful for testing error handling in your application:

```python
def test_error_handling_logic():
    ParamikoMockEnviron().add_responses_for_host('prod_server', 22, {
        'backup_db': SSHCommandMock('', 'Database backed up successfully', '', exit_status=0),
        'backup_db --fail': SSHCommandMock('', '', 'Backup failed: insufficient space', exit_status=1),
        'check_service': SSHCommandMock('', 'Service is running', '', exit_status=0),
        'check_service --down': SSHCommandMock('', '', 'Service is not running', exit_status=3)
    }, 'admin', 'secret')

    def backup_and_check():
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('prod_server', port=22, username='admin', password='secret')
        
        # Try backup
        stdin, stdout, stderr = client.exec_command('backup_db')
        backup_status = stderr.channel.recv_exit_status()
        
        if backup_status != 0:
            print(f"Backup failed: {stderr.read().decode()}")
            return False
        
        # Check service status
        stdin, stdout, stderr = client.exec_command('check_service')
        service_status = stderr.channel.recv_exit_status()
        
        if service_status != 0:
            print(f"Service check failed: {stderr.read().decode()}")
            return False
        
        print("All operations completed successfully")
        return True

    with patch('paramiko.SSHClient', new=SSHClientMock):
        # Test successful scenario
        success = backup_and_check()
        assert success == True
        
        # Test failure scenario
        ParamikoMockEnviron().add_responses_for_host('prod_server', 22, {
            'backup_db': SSHCommandMock('', '', 'Backup failed: insufficient space', exit_status=1),
            'check_service': SSHCommandMock('', 'Service is running', '', exit_status=0)
        }, 'admin', 'secret')
        
        success = backup_and_check()
        assert success == False
    
    ParamikoMockEnviron().cleanup_environment()
```

## Exit Status with Regular Expressions

Exit status works with regular expressions just like other SSH command mocking:

```python
def test_exit_status_with_regex():
    ParamikoMockEnviron().add_responses_for_host('web_server', 22, {
        're(httpd.*)': SSHCommandMock('', 'HTTP server running', '', exit_status=0),
        're(fail.*)': SSHCommandMock('', '', 'Command execution failed', exit_status=1),
        're(docker ps.*)': SSHCommandMock('', 'container1\ncontainer2', '', exit_status=0),
        're(docker stop.*)': SSHCommandMock('', '', 'Error: container not found', exit_status=125)
    }, 'user', 'pass')

    with patch('paramiko.SSHClient', new=SSHClientMock):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('web_server', port=22, username='user', password='pass')
        
        # These will match the regex patterns and return appropriate exit statuses
        commands_to_test = [
            'httpd status',      # Matches 're(httpd.*)' -> exit_status 0
            'fail_command',      # Matches 're(fail.*)' -> exit_status 1
            'docker ps -a',      # Matches 're(docker ps.*)' -> exit_status 0
            'docker stop missing' # Matches 're(docker stop.*)' -> exit_status 125
        ]
        
        for cmd in commands_to_test:
            stdin, stdout, stderr = client.exec_command(cmd)
            exit_status = stderr.channel.recv_exit_status()
            print(f"Command '{cmd}' -> exit status: {exit_status}")
    
    ParamikoMockEnviron().cleanup_environment()
```

## Complete Example

Here's a comprehensive example demonstrating exit status testing:

```python
from paramiko_mock import (
    SSHCommandMock, ParamikoMockEnviron,
    SSHClientMock
)
from unittest.mock import patch
import paramiko

def example_application_function_with_exit_status():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        'example_host', 
        port=22, 
        username='user', 
        password='pass'
    )
    
    # Execute a command that should succeed
    stdin, stdout, stderr = client.exec_command('ls -l')
    exit_status = stderr.channel.recv_exit_status()
    
    if exit_status == 0:
        print(f"Command succeeded with exit status {exit_status}")
        print(f"Output: {stdout.read().decode()}")
    else:
        print(f"Command failed with exit status {exit_status}")
        print(f"Error: {stderr.read().decode()}")
    
    # Execute a command that should fail
    stdin, stdout, stderr = client.exec_command('cat nonexistent_file.txt')
    exit_status = stderr.channel.recv_exit_status()
    
    if exit_status == 0:
        print(f"Command succeeded with exit status {exit_status}")
        print(f"Output: {stdout.read().decode()}")
    else:
        print(f"Command failed with exit status {exit_status}")
        print(f"Error: {stderr.read().decode()}")

def test_example_application_function_with_exit_status():
    # Set up mock responses with different exit statuses
    ParamikoMockEnviron().add_responses_for_host('example_host', 22, {
        'ls -l': SSHCommandMock('', 'file1.txt\nfile2.txt\ndir1/', '', exit_status=0),
        'cat nonexistent_file.txt': SSHCommandMock('', '', 'cat: nonexistent_file.txt: No such file or directory', exit_status=1)
    }, 'user', 'pass')

    with patch('paramiko.SSHClient', new=SSHClientMock):
        example_application_function_with_exit_status()
        
        # Verify commands were executed
        ParamikoMockEnviron().assert_command_was_executed('example_host', 22, 'ls -l')
        ParamikoMockEnviron().assert_command_was_executed('example_host', 22, 'cat nonexistent_file.txt')
        
    ParamikoMockEnviron().cleanup_environment()
```

## Standard Exit Status Codes

Here are some common exit status codes you might want to test:

| Exit Status | Meaning | Common Use Case |
|-------------|---------|-----------------|
| 0 | Success | Command completed successfully |
| 1 | General error | Catch-all for various errors |
| 2 | Misuse of shell builtins | Incorrect command usage |
| 126 | Command cannot execute | Permission denied or command not executable |
| 127 | Command not found | Command doesn't exist |
| 128 | Invalid exit argument | Exit command with invalid argument |
| 128+n | Fatal error signal n | Command killed by signal |
| 130 | Script terminated by Control-C | User interrupted command |
| 255 | Exit status out of range | Exit code outside valid range |

## Best Practices

1. **Test both success and failure scenarios**: Always test how your application handles both successful commands (exit status 0) and various failure scenarios.

2. **Use realistic exit codes**: Use exit status codes that match what the actual commands would return in production.

3. **Test error message handling**: Combine exit status testing with stderr output to ensure your application properly handles error messages.

4. **Verify command execution**: Use `assert_command_was_executed()` to ensure the expected commands were actually called.

5. **Clean up environment**: Always call `cleanup_environment()` after each test to avoid interference between tests.

Exit status testing is essential for building robust applications that can handle command failures gracefully and provide appropriate error handling and user feedback.
