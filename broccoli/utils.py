import asyncio
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
