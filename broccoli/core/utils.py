import asyncio
import contextlib
import zmq

async def any_finished(*aws):
    """ When first completed, return a tuple of bools indicating which tasks
    are complete. Cancels and awaits the incomplete tasks (so wrap any tasks
    that should continue with shield). """
    done, pending = await asyncio.wait(aws, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
    return tuple(aw in done for aw in aws)

def simple_subscriber(context, address):
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b"")
    socket.connect(address)
    return socket
