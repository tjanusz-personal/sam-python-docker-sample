import pytest 
from unittest import TestCase

# Had to manually add the ecshelpers to the test path
import sys, os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../ecshelpers/')
print(sys.path)


'''
Common pytest fixtures to be used across all unit tests.
'''

# define some fixtures to make code cleaner
@pytest.fixture
def assertions():
    return TestCase()

# add my custom markers I need
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "aws_integration: mark test to run only on named environment"
    )

# add a default option for aws_integration tests
def pytest_addoption(parser):
    parser.addoption(
        "--aws_integration", action="store_true", default=False, help="run tests integrated w/aws account"
    )

# override the tests collection to skip the aws_integration ones by default
def pytest_collection_modifyitems(config, items):
    if config.getoption("--aws_integration"):
        return
    skip_aws = pytest.mark.skip(reason="need --aws_integration option to run")
    for item in items:
        if "aws_integration" in item.keywords:
            item.add_marker(skip_aws)