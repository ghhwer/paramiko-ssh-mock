# Advanced Usage

This section covers advanced usage patterns and techniques for working with ParamikoMock, including extending unittest.TestCase, custom response classes, and complex testing scenarios.

## Using it as an extended class of `unittest.TestCase`

You can setup a test case that extends `unittest.TestCase` and uses the `ParamikoMock` class to manage the mock environment. This approach provides better organization and automatic setup/teardown for your tests.

### Basic TestCase Extension

```python
import unittest
import pytest
from unittest.mock import patch
from src.paramiko_mock import (SSHClientMock, ParamikoMockEnviron, SSHCommandMock)
import paramiko

def my_application_code():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Some example of connection
    client.connect('some_host',
                    port=22,
                    username='root',
                    password='root',
                    banner_timeout=10)
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
        assert output == 'ls -l output'
```

### Advanced TestCase with Multiple Hosts

```python
import unittest
from unittest.mock import patch
from paramiko_mock import (
    SSHClientMock, ParamikoMockEnviron, SSHCommandMock,
    LocalFileMock, SFTPFileMock
)
import paramiko

class AdvancedParamikoMockTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment for all tests in the class"""
        # Setup multiple hosts with different configurations
        ParamikoMockEnviron().add_responses_for_host(
            host='web-server.example.com', 
            port=22, 
            responses={
                'nginx -t': SSHCommandMock('', 'nginx: configuration file test is successful', ''),
                'systemctl reload nginx': SSHCommandMock('', '', ''),
            }, 
            username='webadmin', 
            password='webpass'
        )
        
        ParamikoMockEnviron().add_responses_for_host(
            host='db-server.example.com', 
            port=22, 
            responses={
                'mysql -u root -p -e "SHOW DATABASES;"': SSHCommandMock('', 'information_schema\nmysql\nperformance_schema\ntest_db', ''),
                'mysqldump test_db': SSHCommandMock('', '-- MySQL dump', '', exit_status=0),
            }, 
            username='dbadmin', 
            password='dbpass'
        )
        
        # Setup SFTP files
        remote_config = SFTPFileMock()
        remote_config.file_content = 'server_name example.com;\nlisten 80;'
        ParamikoMockEnviron().add_mock_file_for_host('web-server.example.com', 22, '/etc/nginx/nginx.conf', remote_config)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment after all tests"""
        ParamikoMockEnviron().cleanup_environment()
    
    def setUp(self):
        """Set up for each individual test"""
        # Reset any test-specific state if needed
        pass
    
    def test_web_server_operations(self):
        """Test web server SSH operations"""
        def configure_web_server():
            client = paramiko.SSHClient()
            client.connect('web-server.example.com', port=22, username='webadmin', password='webpass')
            
            # Test nginx configuration
            stdin, stdout, stderr = client.exec_command('nginx -t')
            result = stdout.read().decode()
            
            # Reload nginx if config is valid
            if 'successful' in result:
                stdin, stdout, stderr = client.exec_command('systemctl reload nginx')
            
            return result
        
        with patch('paramiko.SSHClient', new=SSHClientMock):
            result = configure_web_server()
            assert 'successful' in result
            ParamikoMockEnviron().assert_command_was_executed('web-server.example.com', 22, 'nginx -t')
    
    def test_database_operations(self):
        """Test database SSH operations"""
        def backup_database():
            client = paramiko.SSHClient()
            client.connect('db-server.example.com', port=22, username='dbadmin', password='dbpass')
            
            # List databases
            stdin, stdout, stderr = client.exec_command('mysql -u root -p -e "SHOW DATABASES;"')
            databases = stdout.read().decode()
            
            # Backup specific database
            stdin, stdout, stderr = client.exec_command('mysqldump test_db')
            backup = stdout.read().decode()
            
            return databases, backup
        
        with patch('paramiko.SSHClient', new=SSHClientMock):
            databases, backup = backup_database()
            assert 'test_db' in databases
            assert 'MySQL dump' in backup
```

## Custom Response Classes

### Creating Custom SSH Response Classes

You can create custom response classes that extend `SSHResponseMock` to implement complex logic:

```python
from paramiko_mock import (
    SSHResponseMock, 
    ParamikoMockEnviron,
    SSHClientMock,
    StderrMock,
    ChannelMock
)
from io import BytesIO
import json
import time

class DynamicResponseMock(SSHResponseMock):
    """Custom response class that generates dynamic responses based on command"""
    
    def __init__(self, response_generator=None):
        self.response_generator = response_generator or self.default_generator
    
    def default_generator(self, ssh_client_mock, command):
        """Default response generator"""
        host = ssh_client_mock.device.host
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        stderr = StderrMock(b"", 0)
        if 'status' in command:
            return (BytesIO(), BytesIO(f"Status OK on {host} at {timestamp}".encode()), stderr)
        elif 'version' in command:
            return (BytesIO(), BytesIO(f"Version 1.0.0 (built on {timestamp})".encode()), stderr)
        else:
            return (BytesIO(), BytesIO(f"Command '{command}' executed on {host}".encode()), stderr)
    
    def __call__(self, ssh_client_mock: SSHClientMock, command: str) -> tuple[BytesIO, BytesIO, BytesIO]:
        return self.response_generator(ssh_client_mock, command)

class JSONResponseMock(SSHResponseMock):
    """Custom response class that returns JSON formatted responses"""
    
    def __init__(self, data_dict):
        self.data_dict = data_dict
    
    def __call__(self, ssh_client_mock: SSHClientMock, command: str) -> tuple[BytesIO, BytesIO, BytesIO]:
        # Parse command to determine what data to return
        if 'get_user' in command:
            user_data = self.data_dict.get('user', {})
            response = json.dumps(user_data)
        elif 'get_config' in command:
            config_data = self.data_dict.get('config', {})
            response = json.dumps(config_data)
        else:
            response = json.dumps({"error": "Unknown command"})
        
        stderr = StderrMock(b"", 0)
        return (BytesIO(), BytesIO(response.encode()), stderr)

def test_custom_response_classes():
    # Setup with custom response classes
    ParamikoMockEnviron().add_responses_for_host('api-server.example.com', 22, {
        're(status.*)': DynamicResponseMock(),
        're(version.*)': DynamicResponseMock(),
        'get_user': JSONResponseMock({
            'user': {'id': 123, 'name': 'John Doe', 'email': 'john@example.com'}
        }),
        'get_config': JSONResponseMock({
            'config': {'debug': True, 'port': 8080, 'timeout': 30}
        })
    }, 'apiuser', 'apipass')
    
    def test_api_commands():
        client = paramiko.SSHClient()
        client.connect('api-server.example.com', port=22, username='apiuser', password='apipass')
        
        commands_and_expected = [
            ('status', 'Status OK'),
            ('version', 'Version 1.0.0'),
            ('get_user', 'John Doe'),
            ('get_config', 'debug')
        ]
        
        results = []
        for cmd, expected in commands_and_expected:
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read().decode()
            results.append((cmd, expected in output))
        
        return results
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        results = test_api_commands()
        for cmd, success in results:
            assert success, f"Command '{cmd}' failed"
    
    ParamikoMockEnviron().cleanup_environment()
```

### Stateful Response Classes

Create response classes that maintain state across multiple commands:

```python
class StatefulServiceMock(SSHResponseMock):
    """Mock service that maintains state across commands"""
    
    def __init__(self):
        self.service_status = 'stopped'
        self.service_config = {'port': 8080, 'debug': False}
    
    def __call__(self, ssh_client_mock: SSHClientMock, command: str) -> tuple[BytesIO, BytesIO, BytesIO]:
        stderr = StderrMock(b"", 0)

        if command == 'service status':
            return (BytesIO(), BytesIO(f"Service is {self.service_status}".encode()), stderr)
        
        elif command == 'service start':
            self.service_status = 'running'
            return (BytesIO(), BytesIO("Service started".encode()), stderr)
        
        elif command == 'service stop':
            self.service_status = 'stopped'
            return (BytesIO(), BytesIO("Service stopped".encode()), stderr)
        
        elif command == 'service restart':
            self.service_status = 'running'
            return (BytesIO(), BytesIO("Service restarted".encode()), stderr)
        
        elif 'config set' in command:
            # Parse config set command: config set key=value
            parts = command.split()
            if len(parts) >= 3:
                key_value = parts[2]
                if '=' in key_value:
                    key, value = key_value.split('=', 1)
                    self.service_config[key] = value
                    return (BytesIO(), BytesIO(f"Config set: {key}={value}".encode()), BytesIO())
        
        elif command == 'config show':
            config_str = '\n'.join(f"{k}={v}" for k, v in self.service_config.items())
            return (BytesIO(), BytesIO(config_str.encode()), BytesIO())
        
        else:
            return (BytesIO(), BytesIO("Unknown command".encode()), BytesIO())

def test_stateful_service():
    service_mock = StatefulServiceMock()
    
    ParamikoMockEnviron().add_responses_for_host('service-server.example.com', 22, {
        're(service.*)': service_mock,
        're(config.*)': service_mock
    }, 'serviceuser', 'servicepass')
    
    def manage_service():
        client = paramiko.SSHClient()
        client.connect('service-server.example.com', port=22, username='serviceuser', password='servicepass')
        
        # Check initial status
        stdin, stdout, stderr = client.exec_command('service status')
        initial_status = stdout.read().decode().strip()
        
        # Start service
        stdin, stdout, stderr = client.exec_command('service start')
        start_result = stdout.read().decode().strip()
        
        # Check status after start
        stdin, stdout, stderr = client.exec_command('service status')
        after_start_status = stdout.read().decode().strip()
        
        # Set config
        stdin, stdout, stderr = client.exec_command('config set debug=true')
        config_result = stdout.read().decode().strip()
        
        # Show config
        stdin, stdout, stderr = client.exec_command('config show')
        config_output = stdout.read().decode().strip()
        
        return initial_status, start_result, after_start_status, config_result, config_output
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        results = manage_service()
        
        assert 'stopped' in results[0]
        assert 'started' in results[1]
        assert 'running' in results[2]
        assert 'debug=true' in results[4]
    
    ParamikoMockEnviron().cleanup_environment()
```

## Complex Testing Scenarios

### Multi-Host Workflows

```python
def test_multi_host_deployment():
    """Test deployment workflow across multiple hosts"""
    
    # Setup web server
    ParamikoMockEnviron().add_responses_for_host('web1.example.com', 22, {
        'git pull': SSHCommandMock('', 'Already up to date', ''),
        'npm install': SSHCommandMock('', 'npm packages installed', ''),
        'npm run build': SSHCommandMock('', 'Build completed', ''),
        'systemctl reload nginx': SSHCommandMock('', '', ''),
    }, 'deploy', 'deploy123')
    
    # Setup database server
    ParamikoMockEnviron().add_responses_for_host('db1.example.com', 22, {
        'mysql -u root -p -e "FLUSH PRIVILEGES;"': SSHCommandMock('', '', ''),
        'mysqldump --all-databases': SSHCommandMock('', 'MySQL dump', ''),
    }, 'dbadmin', 'dbpass123')
    
    # Setup load balancer
    ParamikoMockEnviron().add_responses_for_host('lb1.example.com', 22, {
        'haproxy -f /etc/haproxy/haproxy.cfg -c': SSHCommandMock('', 'Configuration file is valid', ''),
        'systemctl reload haproxy': SSHCommandMock('', '', ''),
    }, 'lbadmin', 'lbpass123')
    
    def deploy_application():
        """Deploy application across multiple servers"""
        results = {}
        
        # Deploy to web server
        client = paramiko.SSHClient()
        client.connect('web1.example.com', port=22, username='deploy', password='deploy123')
        
        stdin, stdout, stderr = client.exec_command('git pull')
        results['git_pull'] = stdout.read().decode().strip()
        
        stdin, stdout, stderr = client.exec_command('npm install')
        results['npm_install'] = stdout.read().decode().strip()
        
        stdin, stdout, stderr = client.exec_command('npm run build')
        results['npm_build'] = stdout.read().decode().strip()
        
        client.close()
        
        # Backup database
        client = paramiko.SSHClient()
        client.connect('db1.example.com', port=22, username='dbadmin', password='dbpass123')
        
        stdin, stdout, stderr = client.exec_command('mysqldump --all-databases')
        results['db_backup'] = stdout.read().decode().strip()
        
        client.close()
        
        # Reload load balancer
        client = paramiko.SSHClient()
        client.connect('lb1.example.com', port=22, username='lbadmin', password='lbpass123')
        
        stdin, stdout, stderr = client.exec_command('systemctl reload haproxy')
        results['lb_reload'] = 'reloaded'  # Success if no exception
        
        client.close()
        
        return results
    
    with patch('paramiko.SSHClient', new=SSHClientMock):
        results = deploy_application()
        
        assert 'up to date' in results['git_pull']
        assert 'installed' in results['npm_install']
        assert 'completed' in results['npm_build']
        assert 'MySQL dump' in results['db_backup']
        assert results['lb_reload'] == 'reloaded'
    
    ParamikoMockEnviron().cleanup_environment()
```

## Best Practices for Advanced Usage

1. **Use TestCase inheritance for complex test suites**: This provides better organization and automatic setup/teardown.

2. **Create reusable custom response classes**: Build custom response classes for common patterns in your application.

3. **Test error scenarios**: Include tests for failures, retries, and edge cases.

4. **Maintain test isolation**: Ensure tests don't interfere with each other by proper cleanup.

5. **Use descriptive test names**: Make it clear what each test is verifying.

6. **Mock realistic scenarios**: Create mocks that closely match your actual production environment.

7. **Document complex mocks**: Add comments explaining the purpose and behavior of custom response classes.

Advanced usage patterns allow you to create comprehensive tests that verify complex workflows, error handling, and integration scenarios in your SSH-based applications.
