"""
Client program connects to a PUB channel and executes tasks as described.

    python task-subscriber.py tcp://host:port

Expects either an empty message (b'') indicating that the subscriber should
stop tasks and wait for input, or a msgpacked dict {"task": "task_name"} which
selects the task to run.

Currently synchronous - the task runs until complete and the subscriber does
not check for new messages while a task is running.
"""

import asyncio
import multiprocessing
import logging

import click
import msgpack
import zmq.asyncio


logger = logging
logging.basicConfig(level=logging.DEBUG)


async def stress(seconds, cpus=multiprocessing.cpu_count()):
    logging.info(f"Running the stress task for {seconds} seconds")
    p = await asyncio.create_subprocess_shell(f"stress --cpu {cpus}")
    await asyncio.sleep(seconds)
    p.terminate()
    await p.wait()
    p = await asyncio.create_subprocess_shell("pkill stress")
    await p.wait()
    return 0


async def fast_forward(socket, default=None):
    """ Return the latest message waiting on the socket, discarding all
    previous messages. """
    msg = default
    while True:
        waiting = await socket.poll(timeout=0)
        if waiting:
            msg = await socket.recv()
        else:
            return msg


async def launch_task(msg):
    task = msgpack.unpackb(msg, raw=False)["task"]
    if task == "stress":
        await stress(seconds=10)
    else:
        raise ValueError(f"Invalid task description: {task}")


async def client(address):
    logger.info(f"Subscribing to tasks on {address}")
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b"")
    socket.connect(address)
    await socket.poll()
    msg = await fast_forward(socket)
    assert msg is not None
    while True:
        msg = await fast_forward(socket, msg)
        assert msg is not None
        if msg == b"":
            logger.info("Received empty task message. Waiting for further input.")
            await socket.poll()
        else:
            try:
                await launch_task(msg)
            except ValueError as e:
                logging.exception("Invalid message", e)
                logging.info("Waiting for updated message")
                await socket.poll()


@click.command()
@click.argument("address")
def cli(address):
    asyncio.run(client(address))


cli()
