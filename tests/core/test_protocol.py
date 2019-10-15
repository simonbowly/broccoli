import msgpack
import pytest

from broccoli.core import protocol


@pytest.mark.parametrize(
    "content",
    [
        {
            "broccoli_githash": "xxxx",
            "running_floret": {"function": "a", "kwargs": {"a": "b"}},
        }
    ],
)
def test_control_ok(content):
    msg = msgpack.packb(content)
    assert protocol.decode_control_message(msg) == content


@pytest.mark.parametrize(
    "content",
    [
        {"a": "b"},
        {"broccoli_githash": "xxxx"},
        {"broccoli_githash": "xxxx", "running_floret": "xxxx"},
        {"broccoli_githash": "xxxx", "running_floret": {"function": "xxxx"}},
        {
            "broccoli_githash": "xxxx",
            "running_floret": {"function": "xxxx", "kwargs": None},
        },
    ],
)
def test_control_invalid(content):
    msg = msgpack.packb(content)
    with pytest.raises(ValueError):
        protocol.decode_control_message(msg)
