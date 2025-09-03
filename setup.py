# Setup script for the module 'paramiko-mock' located in the 'src' directory.
# The setup script is used to install the module in the local environment.

from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='paramiko-mock',
    version='1.0.2',
    description='Mock for paramiko library',
    author='Caio Cominato',
    author_email='caiopetrellicominato@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'paramiko>=3.4.0'
    ],
    zip_safe=False,
    long_description=long_description,
    long_description_content_type='text/markdown'
)
