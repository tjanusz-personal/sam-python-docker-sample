import json
import pytest
import sys, os


from ecshelpers.ecs_reader import *


def test_do_echo_to_ensure_test_wiring_works(assertions):
    result = do_echo("hello")
    assertions.assertEqual("hello", result)
