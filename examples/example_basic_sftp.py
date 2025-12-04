from paramiko_mock import (
    ParamikoMockEnviron,
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
        
        sftp = client.open_sftp()
        sftp.get('/remote/path/to/file_b.txt', '/local/path/to/file_b.txt')
        sftp.close()

        sftp = client.open_sftp()
        file = sftp.open('/tmp/afileToWrite.txt', 'w')
        file.write('Some content to write')
        file.close()

        sftp.put('/local/path/to/file_a.txt', '/remote/path/to/file_a.txt')
        sftp.close()

def test_example_application_function_sftp():
        ParamikoMockEnviron().add_responses_for_host('myhost.example.ihf', 22, {}, 'root', 'root')
        
        mock_local_file = LocalFileMock()
        mock_local_file.file_content = 'Local file content'
        ParamikoMockEnviron().add_local_file('/local/path/to/file_a.txt', mock_local_file)

        mock_remote_file = SFTPFileMock()
        mock_remote_file.file_content = 'Remote file content'
        ParamikoMockEnviron().add_mock_file_for_host('myhost.example.ihf', 22, '/remote/path/to/file_b.txt', mock_remote_file)
        
        with patch('paramiko.SSHClient', new=SSHClientMock):
                example_application_function_sftp()
                
                file_on_remote = ParamikoMockEnviron().get_mock_file_for_host('myhost.example.ihf', 22, '/remote/path/to/file_a.txt')
                assert file_on_remote.file_content == 'Local file content'
                
                file_on_local = ParamikoMockEnviron().get_local_file('/local/path/to/file_b.txt')
                assert file_on_local.file_content == 'Remote file content'
                
                file_on_remote = ParamikoMockEnviron().get_mock_file_for_host('myhost.example.ihf', 22, '/tmp/afileToWrite.txt')
                assert file_on_remote.file_content == 'Some content to write'
        
        ParamikoMockEnviron().cleanup_environment()