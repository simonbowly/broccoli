import asyncio
import logging

logger = logging.getLogger("broccoli.tasks")


async def run(cmd):
    p = await asyncio.create_subprocess_shell(cmd)
    await p.wait()


async def update_and_restart(commit, status_publisher):
    await status_publisher.send_heartbeat({"state": f"updating to {commit}"})
    await run(f"broccoli-update {commit}")


async def update_required_software(status_publisher):
    await status_publisher.send_heartbeat({"state": "updating software"})
    await status_publisher.send_heartbeat({"state": "updates complete"})
