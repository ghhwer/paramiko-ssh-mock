import unittest
import pytest
from unittest.mock import patch
from src.paramiko_mock import (
    SSHClientMock, ParamikoMockEnviron, SSHCommandMock
)
import paramiko


def my_application_code():
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
        assert output == 'ls -l output'.encode()
