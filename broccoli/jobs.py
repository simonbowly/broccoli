import asyncio
import logging

logger = logging.getLogger("broccoli.tasks")


async def run(cmd):
    logger.info(f"Running {cmd}")
    p = await asyncio.create_subprocess_shell(cmd)
    await p.wait()


async def update_and_restart(commit, status_publisher):
    await status_publisher.send_heartbeat({"state": f"updating to {commit}"})
    await run(f"broccoli-update {commit}")


async def apt_update():
    await run("apt-get update")


async def apt_install(*packages):
    await run("apt-get install -y " + " ".join(packages))


async def update_required_software(status_publisher):
    await status_publisher.send_heartbeat({"state": "updating apt packages"})
    await apt_update()
    await apt_install(
        "bison",
        "build-essential",
        "cmake",
        "flex",
        "git",
        "libgmp-dev",
        "libgsl-dev",
        "libreadline-dev",
        "libxml2-dev",
        "net-tools",
        "pkg-config",
        "python3-dev",
        "python3-pip",
        "stress",
        "wget",
        "zlib1g-dev",
    )
    await status_publisher.send_heartbeat({"state": "updates complete"})
