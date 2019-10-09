#!/usr/bin/env python3.7

"""
Control messages set a required state: broccoli service must match the required
source control version and the specified background task must be running.

A task is interruptible by a control message change, and only one task runs at
a time on the node. A job is run as a one-off.

Node behaviour:
    - A task is always running ('idle' task serves as a dummy)
    - If the service commit does not match the required broccoli version, the
    task is stopped and an update job is run to refresh the code and restart
    the service
    - If the task spec does not match the required task, the task is stopped
    and a new task launched
    - If the latest executed job (by uuid) does not match the end of the job
    queue, the task is stopped and the job queue executed until the head is
    reached
"""

import asyncio
import logging
import pathlib
import subprocess

import click
import msgpack
import psutil
import zmq.asyncio

from . import jobs
from . import tasks
from . import protocol
from . import utils

logger = logging.getLogger("broccoli")
logging.basicConfig(level=logging.INFO)


def restore_to_idle(current_state=None):
    required_state = {
        "commit": current_state["commit"]
        if current_state
        else pathlib.Path("/etc/broccoli/githash").read_text().strip(),
        "task": {"name": "idle", "kwargs": {}},
    }
    current_state = {
        "commit": required_state["commit"],
        "task": {"name": "idle", "kwargs": {}},
    }
    task = tasks.launch_task(**required_state["task"])
    return required_state, current_state, task


def get_resources():
    return {
        "cpu_count": psutil.cpu_count(),
        "cpu_freq": dict(psutil.cpu_freq()._asdict()),
        "cpu_percent": psutil.cpu_percent(),
        "processes": [
            {
                "pid": child.pid,
                "status": child.status(),
                "cmdline": child.cmdline(),
                "mem_percent": child.memory_percent(),
            }
            for child in psutil.Process().children(recursive=True)
        ],
    }


class StatusPublisher:
    def __init__(self, context, address):
        self.socket = context.socket(zmq.PUB)
        self.socket.connect(address)
        self.ip_address = (
            subprocess.check_output(
                r"ifconfig | sed -nE 's| *inet (192.168[0-9\.]+).*|\1|p'", shell=True
            )
            .decode()
            .strip()
        )

    async def send_heartbeat(self, current_state):
        logger.info("sending heartbeat")
        await self.socket.send(
            msgpack.packb(
                dict(
                    current_state, ip_address=self.ip_address, resources=get_resources()
                )
            )
        )

    async def report_error(self, err):
        logger.exception(err)
        await self.socket.send(msgpack.packb({"error": str(err)}))


async def run(context, control_address, status_address):
    control_subscriber = utils.simple_subscriber(context, control_address)
    status_publisher = StatusPublisher(context, status_address)
    await asyncio.sleep(1)
    # Get all external software up to date and kick off the idle task.
    await jobs.update_required_software(status_publisher.send_heartbeat)
    required_state, current_state, task = restore_to_idle()
    while True:
        # Update and restart if a version change is indicated.
        if current_state["commit"] != required_state["commit"]:
            await utils.cancel(task)
            await jobs.update_and_restart(required_state["commit"], status_publisher)
            return
        # Ensure the requested task is running.
        if current_state["task"] != required_state["task"]:
            await utils.cancel(task)
            try:
                task = tasks.launch_task(**required_state["task"])
                current_state["task"] = required_state["task"]
            except Exception as err:
                await status_publisher.report_error(err)
                required_state, current_state, task = restore_to_idle(current_state)
        # Send a heartbeat and listen for control messages.
        await status_publisher.send_heartbeat(current_state)
        poll = control_subscriber.poll()
        done, pending = await asyncio.wait(
            [poll, task], return_when=asyncio.FIRST_COMPLETED, timeout=10
        )
        # Tasks should run forever until interrupted, so this is a reportable error.
        if task in done:
            await status_publisher.report_error("task died")
            required_state, current_state, task = restore_to_idle(current_state)
        # Try to decode messages and update state.
        if poll in done:
            msg = await utils.fast_forward(control_subscriber)
            try:
                required_state = protocol.decode_control(msg)
            except ValueError as err:
                await status_publisher.report_error(err)
        else:
            await utils.cancel(poll)


@click.command()
@click.argument("control-address")
@click.argument("status-address")
def cli(control_address, status_address):
    context = zmq.asyncio.Context()
    asyncio.run(run(context, control_address, status_address))
