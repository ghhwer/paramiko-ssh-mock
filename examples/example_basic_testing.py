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
                assert output_1 == 'ls output'
                assert output_2 == 'docker ps output'
                ParamikoMockEnviron().assert_command_was_executed('myhost.example.ihf', 22, 'ls -l')
                ParamikoMockEnviron().assert_command_was_executed('myhost.example.ihf', 22, 'docker ps')
        
        ParamikoMockEnviron().cleanup_environment()