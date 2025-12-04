"""
Example demonstrating exit status functionality in paramiko-ssh-mock.

This example shows how to use the enhanced SSH mock that supports
exit status through stderr.channel.recv_exit_status(), just like
the real paramiko library.
"""
import paramiko
from paramiko_mock.mocked_env import ParamikoMockEnviron
from paramiko_mock.ssh_mock import SSHClientMock, SSHCommandMock
from unittest.mock import patch


def example_with_exit_status():
    """
    Example function that demonstrates exit status usage.
    This simulates a real-world scenario where you need to check
    the exit status of executed commands.
    """
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('example_host', port=22, username='user', password='pass')
    
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


def main():
    """
    Main function that sets up the mock and runs the example.
    """
    # Set up mock responses with different exit statuses
    ParamikoMockEnviron().add_responses_for_host('example_host', 22, {
        'ls -l': SSHCommandMock('', 'file1.txt\nfile2.txt\ndir1/', '', exit_status=0),
        'cat nonexistent_file.txt': SSHCommandMock('', '', 'cat: nonexistent_file.txt: No such file or directory', exit_status=1)
    }, 'user', 'pass')
    
    # Patch paramiko.SSHClient with our mock
    with patch('paramiko.SSHClient', new=SSHClientMock):
        print("Running example with exit status support...")
        example_with_exit_status()
    
    # Clean up the mock environment
    ParamikoMockEnviron().cleanup_environment()
    print("Example completed successfully!")


if __name__ == '__main__':
    main()
