import asyncio
import functools
import logging

import psutil

logger = logging.getLogger(__name__)


async def idle(seconds=None, error=False):
    if seconds:
        logger.info(
            f"Running idle for {seconds} seconds and "
            f"exiting {'with error' if error else 'normally'}"
        )
        await asyncio.sleep(seconds)
        if error:
            raise ValueError("idle error")
    else:
        logger.info("Running idle forever")
        while True:
            await asyncio.sleep(60)


async def stress(cpus):
    """ Run the linux stress tool as a cancellable coroutine. """
    logger.info(f"Launching {cpus} stress hogs")
    pstress = await asyncio.create_subprocess_exec("stress", "--cpu", str(cpus))
    try:
        await pstress.wait()
    finally:
        pids = [child.pid for child in psutil.Process(pstress.pid).children()]
        logger.info(f"Killing main stress process on pid {pstress.pid}")
        pstress.terminate()
        await pstress.wait()
        for pid in pids:
            logger.info(f"Killing stress hog on pid {pid}")
            pkill = await asyncio.create_subprocess_exec("kill", str(pid))
            await pkill.wait()
        logger.info("Stress hogs stopped")


functions = {
    "idle": idle,
    "stress": functools.partial(stress, cpus=psutil.cpu_count()),
}
