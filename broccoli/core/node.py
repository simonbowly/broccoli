import asyncio
import contextlib
import logging

import zmq.asyncio

from .. import BROCCOLI_GITHASH
from . import florets
from . import protocol
from . import utils

logger = logging.getLogger(__name__)


async def update_system_state():
    pass


async def update_and_restart(commit):
    raise Exception("Update not implemented")


async def wrap_floret(function, kwargs):
    logger.info(f"floret '{function}' starting")
    try:
        await florets.functions[function](**kwargs)
        logger.warning(f"floret '{function}' exited")
    except asyncio.CancelledError:
        logger.info(f"floret '{function}' cancelled")
    except:
        logger.exception(f"floret '{function}' exited with error")


class Controller:
    async def cancel_task(self):
        self.task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self.task

    async def start_task(self, required):
        self.task = asyncio.create_task(wrap_floret(**required))
        self.spec = required


def idle_required_state():
    return {
        "broccoli_githash": BROCCOLI_GITHASH,
        "running_floret": {"function": "idle", "kwargs": {}},
    }


async def run(context, control_address):
    control_subscriber = utils.simple_subscriber(context, control_address)
    try:
        await update_system_state()
    except:
        logger.exception("Failed to update system")
        await update("origin/minimal")
        await restart_stalk()
        # No need? Just set BROCCOLI_GITHASH = f"{BROCCOLI_GITHASH}:safemode"
        # (really this should be a property within run() something, not a global?).
        # Then we enter the idle state and the users 'broccoli_commit' message
        # will force another update. No tasks can be started unless the user
        # explicitly matches the 'safemode' part of the string (and we could
        # make that an invalid message).
        #
        # So in practice - if broccoli cannot get itself into the system state
        # required by the current version, it goes into safe mode which just
        # idles and prevents any tasks from being started. But it stays responsive
        # to updates so the user can correct issues with update_system_state(),
        # issue a new commit and run the update.
        #
        # For users - broccoli.core (future broccoli.stalk) provides the core
        # stable functionality, including safe mode. Don't modify it unless you
        # know what you're doing. Instead, add update_system_state tasks and
        # floret functions to broccoli.florets. The core will attempt to load
        # updaters and task runners from broccoli.florets, but treats them as
        # unstable so it can roll back to safe mode and recover from failed
        # tasks as needed (even module import failures should be fine).
        return
    current_state = Controller()
    required_state = idle_required_state()
    await current_state.start_task(required_state["running_floret"])
    while True:
        message_waiting, task_done = await utils.any_finished(
            control_subscriber.poll(), asyncio.shield(current_state.task)
        )
        if task_done:
            required_state = idle_required_state()
            await current_state.start_task(required_state["running_floret"])
        if message_waiting:
            msg = await control_subscriber.recv()
            try:
                required_state = protocol.decode_control_message(msg)
                logger.debug(f"received required state: {required_state}")
            except:
                logger.exception("Failed to decode control messsage")
            if BROCCOLI_GITHASH != required_state["broccoli_githash"]:
                logger.info(
                    f"Require update {BROCCOLI_GITHASH} -> "
                    + required_state["broccoli_githash"]
                )
                await current_state.cancel_task()
                try:
                    await update(required_state["broccoli_githash"])
                    await restart_stalk()
                    return
                except:
                    logger.exception("Failed to update broccoli")
                    required_state = idle_required_state()
                    await current_state.start_task(required_state["running_floret"])
            if current_state.spec != required_state["running_floret"]:
                await current_state.cancel_task()
                try:
                    await current_state.start_task(required_state["running_floret"])
                except:
                    logger.exception("Failed to start task")
                    required_state = idle_required_state()
                    await current_state.start_task(required_state["running_floret"])


logging.basicConfig(level=logging.DEBUG)
context = zmq.asyncio.Context()
print(BROCCOLI_GITHASH)
asyncio.run(run(context, "tcp://localhost:4444"))
