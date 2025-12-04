# What is ParamikoMock?

This is a mock library for the Paramiko SSH library. It is intended to be used in unit tests to mock SSH connections and commands.
It supports mocking multiple hosts and multiple commands per host as well as SFTP connections.

## How it works?

ParamikoMock is built to be used with `patch` from the `unittest.mock` module. 
We will cover how to use on the [Usage](usage.md) page.

We use the concept of a `Coordinator` class that manages the mock environment. 
The `Coordinator` is a singleton class that manages the mock environment. It is responsible for creating and managing the mock environment.

```mermaid
---
config:
  markdownAutoWrap: true
---
flowchart TD
 subgraph subGraph0["**Coordinator** (_Singleton_)"]
        A(["ParamikoMockEnviron"])
  end
 subgraph subGraph1["**Patched Class**"]
        B(["SSHClientMock"])
        D(["SFTPClientMock"])
  end
 subgraph subGraph2[" "]
        C(["MockRemoteDevice"])
        F(["LocalFilesystemMock"])
        E(["SFTPFileSystem"])
  end
 subgraph subGraph4["**Mock Objects**"]
        G(["SFTPFileMock"])
        H(["LocalFileMock"])
        I(["SSHCommandMock"])
  end
 subgraph s1["ParamikoMock"]
        subGraph0
        subGraph1
        subGraph2
        subGraph4
  end
    B -- Uses --- C
    B -- Opens --- D
    C -- Has --- E & I
    F -- Has --- H
    E -- Has --- G
    D -- Uses --- C & F
    subGraph0 -- Manages --> subGraph2
    style A fill:#aaaafa,stroke:#000,stroke-width:2px
    style B fill:#aafaaa,stroke:#000,stroke-width:2px
    style D fill:#fafaaa,stroke:#000,stroke-width:2px
    style C fill:#aafafa,stroke:#000,stroke-width:2px
    style F fill:#119191,stroke:#000,stroke-width:2px,color:#000000
    style E fill:#119191,stroke:#000,stroke-width:2px,color:#000000
    style G fill:#aaaafa,stroke:#000,stroke-width:2px
    style H fill:#aaaafa,stroke:#000,stroke-width:2px
    style I fill:#aaaafa,stroke:#000,stroke-width:2px
    style subGraph0 stroke:#000000,fill:#d0d0d0,color:#000000
    style subGraph1 stroke:#000000,color:#000000,fill:#FFFFFF
    style subGraph2 stroke:#000000,fill:#FFFFFF,color:#000000
    style subGraph4 stroke:#000000,fill:#d0d0d0,color:#000000
    style s1 stroke:#000000,fill:#FFFFFF
```

Api documentation can be found in the [API Reference](/autoapi/paramiko_mock/) page.
The full implementation can be found in the [GitHub Repository](https://github.com/ghhwer/paramiko-ssh-mock)

## Quick Start

Want to get started quickly? Here is how you can install ParamikoMock:

```bash
pip install paramiko-mock
```

## Usage Examples

ParamikoMock supports various SSH and SFTP operations for testing. Here are the main use cases:

### [Basic SSH Operations](basic-ssh.md)
Learn how to mock basic SSH commands, set up command responses, and use regular expressions for command matching.

### [Exit Status Testing](exit-status.md)
Test how your application handles different command execution outcomes with exit status mocking.

### [Connection Failures Testing](connection-failures.md)
Mock various connection failure scenarios like DNS resolution failures, timeouts, and authentication errors.

### [SFTP Operations](sftp-operations.md)
Mock file transfer operations including uploads, downloads, and remote file management.

### [Advanced Usage](advanced-usage.md)
Explore advanced patterns like custom response classes, unittest.TestCase integration, and complex testing scenarios.

For a complete overview of all available features, see the [Usage](usage.md) page.
