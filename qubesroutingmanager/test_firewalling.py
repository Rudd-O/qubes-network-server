import os

from unittest import mock
from qubesroutingmanager import setup_plain_forwarding_for_address


def get_fixture(name):
    with open(os.path.join(os.path.dirname(__file__), "fixtures", name)) as f:
        return f.read()


def mock_collector(output: str):
    final_args = []

    class MockedPopen:
        def __init__(self, args, **kwargs):
            final_args.append(args[3:])
            self.args = args
            self.returncode = 0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, value, traceback):
            pass

        def communicate(self, input=None, timeout=None):
            stdout = output
            stderr = ""
            self.returncode = 1
            return stdout, stderr

        def poll(self):
            return 0

    return final_args, MockedPopen


def test_partial_add_completes_the_add():
    got, MockedPopen = mock_collector(get_fixture("partially_added.json"))
    expected = [
        ["list", "table", "ip", "qubes"],
        ["add", "chain", "ip", "qubes", "qubes-routing-manager-postrouting"],
        [
            "add",
            "rule",
            "ip",
            "qubes",
            "qubes-routing-manager-postrouting",
            "counter",
        ],
        [
            "add",
            "rule",
            "ip",
            "qubes",
            "postrouting",
            "position",
            "66",
            "jump",
            "qubes-routing-manager-postrouting",
        ],
        [
            "add",
            "rule",
            "ip",
            "qubes",
            "qubes-routing-manager-postrouting",
            "ip",
            "saddr",
            "10.250.4.13",
            "accept",
        ],
    ]
    with mock.patch("subprocess.Popen", MockedPopen):
        setup_plain_forwarding_for_address("10.250.4.13", True, 4)

    assert got == expected


def test_forwarding_does_not_add_twice():
    got, MockedPopen = mock_collector(get_fixture("fully_added.json"))
    expected = [
        ["list", "table", "ip", "qubes"],
    ]
    with mock.patch("subprocess.Popen", MockedPopen):
        setup_plain_forwarding_for_address("10.250.4.13", True, 4)

    assert got == expected
