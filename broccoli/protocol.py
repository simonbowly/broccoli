import msgpack

"""
Controller messages:
{
    # broccoli version that should be running
    "commit": "read from /etc/broccoli/githash",
    # a queue of jobs to run
    "job_queue": [{"uuid": "xxx", "name": "xxx", "kwargs": {"k": "v"}}],
    # name and config of background task that should be running
    "task": {"name": "xxxxxx", "kwargs": {"k": "v"}},
}
"""


def decode_control(msg):
    decoded = msgpack.unpackb(msg, raw=False)
    if "commit" not in decoded:
        raise ValueError("missing commit")
    if "task" not in decoded:
        raise ValueError("missing task")
    if "name" not in decoded["task"]:
        raise ValueError("missing task name")
    if "kwargs" not in decoded["task"]:
        raise ValueError("missing task kwargs")
    return decoded
