
import logging

logger = logging.getLogger("broccoli.tasks")

async def update_required_software(status_publisher):
    pass

async def update_and_restart(commit, status_publisher):
    logger.info(f"Updating to {commit}")
    p = await asyncio.create_subprocess_exec(f"broccoli-update {commit}")
    await p.wait()
