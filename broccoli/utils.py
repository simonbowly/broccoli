import asyncio
import subprocess
import zmq


async def cancel(task):
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def fast_forward(socket):
    """ Return the latest message waiting on the socket, discarding all
    previous messages. Assumes one is available (poll() already called). """
    msg = None
    while True:
        waiting = await socket.poll(timeout=0)
        if waiting:
            msg = await socket.recv()
        else:
            assert msg is not None
            return msg


def simple_subscriber(context, address):
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b"")
    socket.connect(address)
    return socket


async def check(p, cmd):
    retcode = await p.wait()
    if retcode:
        raise subprocess.CalledProcessError(retcode, cmd)


async def run(cmd, *args, cwd=None):
    """
    Behaves like subprocess.check_call. Raises subprocess.CalledProcessError
    for nonzero return codes, and FileNotFoundError if the command is not
    runnable.
    """
    p = await asyncio.create_subprocess_exec(cmd, *args, cwd=cwd)
    await check(p, (cmd,) + args)


async def run_shell(cmd, cwd=None):
    """
    Behaves like subprocess.check_call(cmd, shell=True).
    Raises subprocess.CalledProcessError for nonzero return codes.
    """
    p = await asyncio.create_subprocess_shell(cmd, cwd=cwd)
    await check(p, cmd)
