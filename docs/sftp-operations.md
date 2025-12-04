# SFTP Operations

ParamikoMock provides comprehensive support for mocking SFTP (SSH File Transfer Protocol) operations, allowing you to test file transfer functionality without requiring actual SSH connections or file systems.

## Setting up SFTP Environment

The `ParamikoMockEnviron` class can be used to manage the environment for SFTP operations.
You should use the `LocalFileMock` class to define the local files and the `SFTPFileMock` class to define the remote files.

### Basic SFTP Setup

```python
from paramiko_mock import (
    SSHCommandMock, ParamikoMockEnviron,
    LocalFileMock, SSHClientMock, SFTPFileMock
)
from unittest.mock import patch
import paramiko

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
```

### Accessing Mock Files

`ParamikoMockEnviron` also provides interfaces for getting the local and remote files:

```python
# Get the local file
file_on_local = ParamikoMockEnviron().get_local_file('/local/path/to/file_a.txt')
assert file_on_local.file_content == 'Local file content'

# Get the remote file
file_on_remote = ParamikoMockEnviron().get_mock_file_for_host('myhost.example.ihf', 22, '/remote/path/to/file_b.txt')
assert file_on_remote.file_content == 'Remote file content'
```

## Complete SFTP Example

Here is a comprehensive example demonstrating SFTP operations:

```python
from paramiko_mock import (
    SSHCommandMock, ParamikoMockEnviron,
    LocalFileMock, SSHClientMock, SFTPFileMock
)
from unittest.mock import patch
import paramiko

def example_application_function_sftp():
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
    
    # Download file from remote to local
    sftp = client.open_sftp()
    sftp.get('/remote/path/to/file_b.txt', '/local/path/to/file_b.txt')
    sftp.close()

    # Write content to a remote file
    sftp = client.open_sftp()
    file = sftp.open('/tmp/afileToWrite.txt', 'w')
    file.write('Some content to write')
    file.close()

    # Upload file from local to remote
    sftp.put('/local/path/to/file_a.txt', '/remote/path/to/file_a.txt')
    sftp.close()

def test_example_application_function_sftp():
    ParamikoMockEnviron().add_responses_for_host('myhost.example.ihf', 22, {}, 'root', 'root')
    
    # Setup local file for upload
    mock_local_file = LocalFileMock()
    mock_local_file.file_content = 'Local file content'
    ParamikoMockEnviron().add_local_file('/local/path/to/file_a.txt', mock_local_file)

    # Setup remote file for download
    mock_remote_file = SFTPFileMock()
    mock_remote_file.file_content = 'Remote file content'
    ParamikoMockEnviron().add_mock_file_for_host('myhost.example.ihf', 22, '/remote/path/to/file_b.txt', mock_remote_file)
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        example_application_function_sftp()
        
        # Verify file was uploaded to remote
        file_on_remote = ParamikoMockEnviron().get_mock_file_for_host('myhost.example.ihf', 22, '/remote/path/to/file_a.txt')
        assert file_on_remote.file_content == 'Local file content'
        
        # Verify file was downloaded to local
        file_on_local = ParamikoMockEnviron().get_local_file('/local/path/to/file_b.txt')
        assert file_on_local.file_content == 'Remote file content'
        
        # Verify file was written on remote
        file_on_remote = ParamikoMockEnviron().get_mock_file_for_host('myhost.example.ihf', 22, '/tmp/afileToWrite.txt')
        assert file_on_remote.file_content == 'Some content to write'
    
    ParamikoMockEnviron().cleanup_environment()
```

## SFTP File Operations

### Reading Remote Files

```python
def test_reading_remote_files():
    ParamikoMockEnviron().add_responses_for_host('server.example.com', 22, {}, 'user', 'pass')
    
    # Setup remote file
    remote_file = SFTPFileMock()
    remote_file.file_content = 'This is remote file content\nLine 2\nLine 3'
    ParamikoMockEnviron().add_mock_file_for_host('server.example.com', 22, '/remote/data.txt', remote_file)
    
    def read_remote_file():
        client = paramiko.SSHClient()
        client.connect('server.example.com', port=22, username='user', password='pass')
        sftp = client.open_sftp()
        
        with sftp.open('/remote/data.txt', 'r') as f:
            content = f.read()
        
        sftp.close()
        return content
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        content = read_remote_file()
        assert content == 'This is remote file content\nLine 2\nLine 3'
    
    ParamikoMockEnviron().cleanup_environment()
```

### Writing Remote Files

```python
def test_writing_remote_files():
    ParamikoMockEnviron().add_responses_for_host('server.example.com', 22, {}, 'user', 'pass')
    
    def write_remote_file():
        client = paramiko.SSHClient()
        client.connect('server.example.com', port=22, username='user', password='pass')
        sftp = client.open_sftp()
        
        with sftp.open('/remote/output.txt', 'w') as f:
            f.write('New content written remotely')
        
        sftp.close()
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        write_remote_file()
        
        # Verify the file was written
        remote_file = ParamikoMockEnviron().get_mock_file_for_host('server.example.com', 22, '/remote/output.txt')
        assert remote_file.file_content == 'New content written remotely'
    
    ParamikoMockEnviron().cleanup_environment()
```

### File Upload and Download

```python
def test_file_upload_download():
    ParamikoMockEnviron().add_responses_for_host('server.example.com', 22, {}, 'user', 'pass')
    
    # Setup local file for upload
    local_file = LocalFileMock()
    local_file.file_content = 'Content to upload'
    ParamikoMockEnviron().add_local_file('/local/upload.txt', local_file)
    
    # Setup remote file for download
    remote_file = SFTPFileMock()
    remote_file.file_content = 'Content to download'
    ParamikoMockEnviron().add_mock_file_for_host('server.example.com', 22, '/remote/download.txt', remote_file)
    
    def transfer_files():
        client = paramiko.SSHClient()
        client.connect('server.example.com', port=22, username='user', password='pass')
        sftp = client.open_sftp()
        
        # Upload local file to remote
        sftp.put('/local/upload.txt', '/remote/uploaded.txt')
        
        # Download remote file to local
        sftp.get('/remote/download.txt', '/local/downloaded.txt')
        
        sftp.close()
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        transfer_files()
        
        # Verify upload
        uploaded_file = ParamikoMockEnviron().get_mock_file_for_host('server.example.com', 22, '/remote/uploaded.txt')
        assert uploaded_file.file_content == 'Content to upload'
        
        # Verify download
        downloaded_file = ParamikoMockEnviron().get_local_file('/local/downloaded.txt')
        assert downloaded_file.file_content == 'Content to download'
    
    ParamikoMockEnviron().cleanup_environment()
```

## Advanced SFTP Operations

### File Attributes and Metadata

```python
def test_file_attributes():
    ParamikoMockEnviron().add_responses_for_host('server.example.com', 22, {}, 'user', 'pass')
    
    # Setup remote file with custom attributes
    remote_file = SFTPFileMock()
    remote_file.file_content = 'File with metadata'
    remote_file.st_size = 100  # File size
    remote_file.st_mtime = 1640995200  # Modification time
    ParamikoMockEnviron().add_mock_file_for_host('server.example.com', 22, '/remote/metadata.txt', remote_file)
    
    def check_file_attributes():
        client = paramiko.SSHClient()
        client.connect('server.example.com', port=22, username='user', password='pass')
        sftp = client.open_sftp()
        
        # Get file attributes
        attrs = sftp.stat('/remote/metadata.txt')
        
        sftp.close()
        return attrs.st_size, attrs.st_mtime
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        size, mtime = check_file_attributes()
        assert size == 100
        assert mtime == 1640995200
    
    ParamikoMockEnviron().cleanup_environment()
```

### Directory Operations

```python
def test_directory_operations():
    ParamikoMockEnviron().add_responses_for_host('server.example.com', 22, {}, 'user', 'pass')
    
    def create_and_list_directories():
        client = paramiko.SSHClient()
        client.connect('server.example.com', port=22, username='user', password='pass')
        sftp = client.open_sftp()
        
        # Create directory
        try:
            sftp.mkdir('/remote/new_directory')
        except:
            pass  # Directory might already exist
        
        # List directory contents
        try:
            contents = sftp.listdir('/remote')
        except:
            contents = []  # Handle if directory doesn't exist
        
        sftp.close()
        return contents
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        contents = create_and_list_directories()
        # Verify directory operations work (specific contents depend on implementation)
    
    ParamikoMockEnviron().cleanup_environment()
```

## Error Handling

### File Not Found

```python
def test_file_not_found():
    ParamikoMockEnviron().add_responses_for_host('server.example.com', 22, {}, 'user', 'pass')
    
    def try_read_nonexistent_file():
        client = paramiko.SSHClient()
        client.connect('server.example.com', port=22, username='user', password='pass')
        sftp = client.open_sftp()
        
        try:
            with sftp.open('/remote/nonexistent.txt', 'r') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            return "File not found"
        finally:
            sftp.close()
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        result = try_read_nonexistent_file()
        assert result == "File not found"
    
    ParamikoMockEnviron().cleanup_environment()
```

## Best Practices

1. **Always clean up the environment**: Use `ParamikoMockEnviron().cleanup_environment()` after each test to avoid interference.

2. **Mock both local and remote files**: For upload/download operations, ensure both source and destination files are properly mocked.

3. **Test file content verification**: After SFTP operations, verify that file contents were transferred correctly.

4. **Handle file paths consistently**: Use consistent path formats across your tests to avoid path-related issues.

5. **Test error scenarios**: Include tests for file not found, permission denied, and other error conditions.

6. **Use realistic file content**: Test with various file sizes and content types to ensure your application handles different scenarios.

SFTP mocking with ParamikoMock allows you to thoroughly test file transfer functionality without the complexity of setting up actual SSH servers or managing real file systems.
