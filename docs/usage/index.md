# Usage

ParamikoMock aims to provide a simple way to mock the paramiko library for testing purposes. 
It is designed to be used in unit tests, where the actual connection to a remote host is needed.

When using ParamikoMock you will only need to interact with the following classes:

- `ParamikoMockEnviron` - Provides an interface to manage the mock environment.
- `LocalFileMock` - Provides a mock for local files.
- `SFTPFileMock` - Provides a mock for remote files.
- `SSHCommandMock` - Provides a definition for the output of a command.

The class `SSHClientMock` is used but only for patching the `paramiko.SSHClient` class.

## Feature Overview

ParamikoMock provides comprehensive support for various SSH and SFTP operations. Each feature is documented in detail in the following sections:

### [Basic SSH Operations](basic-ssh.md)
- Setting up mock environments
- Command response mocking
- Regular expression support
- Custom response classes

### [Exit Status Testing](exit-status.md)
- Mocking command exit codes
- Testing error handling logic
- Standard exit status patterns
- Exit status with regular expressions

### [Connection Failures Testing](connection-failures.md)
- DNS resolution failures
- Connection timeouts
- Authentication failures
- Custom exception scenarios
- Mixed success/failure scenarios

### [SFTP Operations](sftp-operations.md)
- File upload and download
- Remote file management
- File attributes and metadata
- Directory operations
- Error handling

### [Advanced Usage](advanced-usage.md)
- unittest.TestCase integration
- Custom response classes
- Stateful mocking
- Multi-host workflows
- Error recovery testing

## Quick Reference

### Basic Setup Pattern

```python
from paramiko_mock import (
    SSHCommandMock, ParamikoMockEnviron,
    SSHClientMock
)
from unittest.mock import patch
import paramiko

# Setup mock environment
ParamikoMockEnviron().add_responses_for_host('host.example.com', 22, {
    'command': SSHCommandMock('', 'output', ''),
}, 'username', 'password')

# Use in your test
with patch('paramiko.SSHClient', new=SSHClientMock):
    # Your application code here
    pass

# Clean up
ParamikoMockEnviron().cleanup_environment()
```

### Key Classes

| Class | Purpose |
|-------|---------|
| `ParamikoMockEnviron` | Manages the mock environment and hosts |
| `SSHCommandMock` | Defines command responses with stdout/stderr |
| `LocalFileMock` | Mocks local files for SFTP operations |
| `SFTPFileMock` | Mocks remote files for SFTP operations |
| `SSHClientMock` | Replacement for `paramiko.SSHClient` in patches |

### Common Methods

| Method | Description |
|--------|-------------|
| `add_responses_for_host()` | Set up mock responses for a host |
| `add_local_file()` | Add a mock local file |
| `add_mock_file_for_host()` | Add a mock remote file |
| `assert_command_was_executed()` | Verify a command was called |
| `cleanup_environment()` | Clean up mock state |

For detailed examples and advanced patterns, please refer to the specific feature documentation linked above.

## Conclusion

ParamikoMock provides a simple way to mock the paramiko library for testing purposes.

It does not provide a full implementation of the paramiko library, but it is designed to be used in unit tests where the actual connection to a remote host is needed.
Contributions are welcome, and you can see how to contribute in the [Contributing Guide](contributing.md).
