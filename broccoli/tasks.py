import asyncio
import logging
import multiprocessing

logger = logging.getLogger("broccoli.tasks")


async def idle():
    logger.info("starting idling task")
    try:
        while True:
            await asyncio.sleep(5)
            logger.info("still idling...")
    except asyncio.CancelledError:
        logger.info("idling task cancelled")


async def stress(cpus=multiprocessing.cpu_count()):
    logger.info(f"Launching stress hogs")
    p1 = await asyncio.create_subprocess_shell(f"stress --cpu {cpus}")
    try:
        await p1.wait()
    except asyncio.CancelledError:
        logger.info(f"Stopping stress hogs")
    p1.terminate()
    p2 = await asyncio.create_subprocess_shell("pkill stress")
    await p2.wait()
    await p1.wait()
    logger.info(f"Stress hogs stopped")


def launch_task(name, kwargs):
    if name == "idle":
        return asyncio.create_task(idle())
    if name == "stress":
        return asyncio.create_task(stress())
    raise ValueError(f"Unknown task: {name}")
