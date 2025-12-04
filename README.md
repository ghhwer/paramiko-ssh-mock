# Paramiko Mock
![Coverage](coverage.svg)

 [![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/ghhwer)

Paramiko Mock is a Python library for mocking the `paramiko` SSH client for testing purposes. It allows you to define responses for specific SSH commands and hosts, making it easier to test code that interacts with remote servers via SSH.

## Version 2.0.0 🚀

We are excited to announce that Paramiko Mock has reached version 2.0.0! 🎉
For more detailed documentation, please visit our [Read the Docs](https://paramiko-ssh-mock.readthedocs.io/en/latest/) page.

## Installation

### Using UV (Recommended)

```bash
# Install UV first (if you haven't already)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the package
uv add paramiko-mock

# Or install from source
uv sync
```

### Using pip

```bash
pip install paramiko-mock
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/ghhwer/paramiko-ssh-mock.git
cd paramiko-ssh-mock

# Install with UV (recommended)
uv sync --dev

# Or with pip
pip install -e .
```

## Usage

Here are some examples of how to use paramiko_mock:

Advanced usage is available [here](https://paramiko-ssh-mock.readthedocs.io/en/latest/usage/) and under the /examples folder.

## Contributing

Contributions are welcome. 
Please work on filing an issue before submitting a pull request, so that we can discuss the changes you would like to make.

[Github](https://github.com/ghhwer/paramiko-ssh-mock)

## License

[MIT](https://choosealicense.com/licenses/mit/)
