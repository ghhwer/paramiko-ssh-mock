import paramiko
from src.ParamikoMock.mocked_env import ParamikoMockEnviron
from src.ParamikoMock.ssh_mock import SSHClientMock
from src.ParamikoMock.sftp_mock import SFTPFileMock 
from src.ParamikoMock.local_filesystem_mock import LocalFileMock
from unittest.mock import patch

# Functions below are examples of what an application could look like
def example_function_sftp_write():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Some example of connection
    client.connect('some_host_4',
                    port=22,
                    username='root',
                    password='root',
                    banner_timeout=10)
    # Some example of a remote file write
    sftp = client.open_sftp()
    file = sftp.open('/tmp/afileToWrite.txt', 'w')
    file.write('Something to put in the remote file')
    file.close()
    sftp.close()

def example_function_sftp_read():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Some example of connection
    client.connect('some_host_4',
                    port=22,
                    username='root',
                    password='root',
                    banner_timeout=10)
    # Some example of a remote file write
    sftp = client.open_sftp()
    file = sftp.open('/tmp/afileToRead.txt', 'r')
    output = file.read()
    file.close()
    sftp.close()
    return output

def example_function_sftp_put():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Some example of connection
    client.connect('some_host_4',
                    port=22,
                    username='root',
                    password='root',
                    banner_timeout=10)
    # Some example of a remote file write
    sftp = client.open_sftp()
    sftp.put('/local/path/to/file_a.txt', '/remote/path/to/file_a.txt')
    sftp.close()

def example_function_sftp_get():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Some example of connection
    client.connect('some_host_4',
                    port=22,
                    username='root',
                    password='root',
                    banner_timeout=10)
    # Some example of a remote file write
    sftp = client.open_sftp()
    sftp.get('/remote/path/to/file_b.txt', '/local/path/to/file_b.txt')
    sftp.close()


def example_function_sftp_list():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Some example of connection
    client.connect('some_host_4',
                    port=22,
                    username='root',
                    password='root',
                    banner_timeout=10)
    # Some example of a remote file write
    sftp = client.open_sftp()
    outut = sftp.listdir('directory_1')
    sftp.close()
    return outut

# Actual tests
# -- This ensures that the ParamikoMock is working as expected
def test_example_function_sftp_write():
    # Setup the mock environment
    ParamikoMockEnviron().add_responses_for_host('some_host_4', 22, {}, 'root', 'root')
    # patch the paramiko.SSHClient with the mock
    with patch('paramiko.SSHClient', new=SSHClientMock): 
        example_function_sftp_write()
        # Get the file content from the mock filesystem
        mock_file = ParamikoMockEnviron().get_mock_file_for_host('some_host_4', 22, '/tmp/afileToWrite.txt')
        # Check if the content is the same as the one written
        assert 'Something to put in the remote file' == mock_file.file_content
    ParamikoMockEnviron().cleanup_environment()

def test_example_function_sftp_read():
    # Setup the mock environment
    ParamikoMockEnviron().add_responses_for_host('some_host_4', 22, {}, 'root', 'root')
    # Create a mock file to be read
    mock_file = SFTPFileMock()
    mock_file.file_content = 'Something from the remote file'
    # Add the mocked file to the host
    ParamikoMockEnviron().add_mock_file_for_host('some_host_4', 22, '/tmp/afileToRead.txt', mock_file)
    # patch the paramiko.SSHClient with the mock
    with patch('paramiko.SSHClient', new=SSHClientMock): 
        output = example_function_sftp_read()
        assert 'Something from the remote file' == output
    ParamikoMockEnviron().cleanup_environment()

def test_example_function_sftp_put():
    # Setup the mock environment
    ParamikoMockEnviron().add_responses_for_host('some_host_4', 22, {}, 'root', 'root')
    # Create a mock file to be read
    mock_local_file = LocalFileMock()
    mock_local_file.file_content = 'Content of the local file'
    # Add the mocked file to the local filesystem
    ParamikoMockEnviron().add_local_file("/local/path/to/file_a.txt", mock_local_file)
    # patch the paramiko.SSHClient with the mock
    with patch('paramiko.SSHClient', new=SSHClientMock): 
        example_function_sftp_put()
        # Get the file content from the mock filesystem
        mock_file = ParamikoMockEnviron().get_mock_file_for_host('some_host_4', 22, '/remote/path/to/file_a.txt')
        # Check if the content is the same as the one written
        assert 'Content of the local file' == mock_file.file_content
    ParamikoMockEnviron().cleanup_environment()

def test_example_function_sftp_get():
    # Setup the mock environment
    ParamikoMockEnviron().add_responses_for_host('some_host_4', 22, {}, 'root', 'root')
    # Create a mock file to be read
    mock_file = SFTPFileMock()
    mock_file.file_content = 'Content of the remote file'
    # Add the mocked file to the host
    ParamikoMockEnviron().add_mock_file_for_host('some_host_4', 22, '/remote/path/to/file_b.txt', mock_file)
    # patch the paramiko.SSHClient with the mock
    with patch('paramiko.SSHClient', new=SSHClientMock): 
        example_function_sftp_get()
        # Get the file content from the mock filesystem
        mock_local_file = ParamikoMockEnviron().get_local_file("/local/path/to/file_b.txt")
        # Check if the content is the same as the one written
        assert 'Content of the remote file' == mock_local_file.file_content
    ParamikoMockEnviron().cleanup_environment()

def test_example_function_sftp_list():

    ParamikoMockEnviron().add_responses_for_host('some_host_4', 22, {}, 'root', 'root')

    files = ["file-a.txt", "directory_1/file-b.txt", "directory_1/file-c.txt"]
    for file in files:
        ParamikoMockEnviron().add_mock_file_for_host('some_host_4', 22, file, LocalFileMock())

    with patch('paramiko.SSHClient', new=SSHClientMock): 
        file_list = example_function_sftp_list()

        assert file_list == ["file-b.txt", "file-c.txt"]

    ParamikoMockEnviron().cleanup_environment()
