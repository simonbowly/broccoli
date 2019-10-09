import json
import logging
import multiprocessing
import os
import shutil

import asyncio
import pathlib

from .utils import run

logger = logging.getLogger("broccoli.tasks")
host = "192.168.1.101"
cores = multiprocessing.cpu_count()
src_dir = "/usr/local/src"
here = pathlib.Path(__file__).parent


async def update_and_restart(commit, status_publisher):
    await status_publisher.send_heartbeat({"state": f"updating to {commit}"})
    await run("broccoli-update", commit)


async def apt_update():
    await run("apt-get", "update", "-q")


async def apt_install(*packages):
    await run("apt-get", "install", "-q", "-y", *packages)


async def git_checkout(repo_url, ref="master", base="."):
    base = pathlib.Path(base)
    _, _, name = repo_url.rpartition("/")
    target = base / name.replace(".git", "")
    if not target.exists():
        await run("git", "clone", repo_url, cwd=base)
    await run("git", "checkout", "master", cwd=target)
    await run("git", "reset", "--hard", ref, cwd=target)
    return target


async def cmake(path, install=True, release=True, flags=None):
    build_dir = path / "build"
    os.makedirs(build_dir, exist_ok=True)
    cmd = ["cmake", ".."]
    if release:
        cmd.append("-DCMAKE_BUILD_TYPE=Release")
    if flags:
        cmd.extend(flags)
    await run(*cmd, cwd=build_dir)
    await run("cmake", "--build", ".", "--clean-first", "-j", str(cores), cwd=build_dir)
    if install:
        await run("cmake", "--build", ".", "--target", "install", cwd=build_dir)


def get_current_installed_versions():
    try:
        return json.loads(pathlib.Path("/etc/broccoli/installed.json").read_text())
    except Exception as err:
        logging.warning("Failed to load software versions file: assuming empty.")
    return {}


def update_current_installed_versions(installed):
    with open("/etc/broccoli/installed.json", "w") as outfile:
        json.dump(installed, outfile, indent=4, sort_keys=True)


async def cmake_git(repo, ref):
    await cmake(await git_checkout(f"git@{host}:{repo}", ref, base=src_dir))


# Targets checked in order so earlier libraries can force a rebuild of later entries.
target_installed = [
    ("rapidcheck", "d9482c6"),
    ("chuffed", "0.10.4"),
    # ("gecode", "release-6.2.0"),
    # ("minizinc", "2.3.2"),
]


async def install(program, version, installed):
    """ As a simple dependency management solution, allow installers to modify
    and return the installed dict, forcing a rebuild of another program. """
    if program == "rapidcheck":
        await cmake_git("emil-e/rapidcheck", version)
        installed[program] = version
    elif program == "chuffed":
        await cmake_git("chuffed/chuffed", version)
        os.makedirs("/usr/local/share/minizinc/solvers", exist_ok=True)
        shutil.copy(
            "/usr/local/src/broccoli/provision/chuffed.msc",
            "/usr/local/share/minizinc/solvers/chuffed.msc",
        )
        installed[program] = version
    elif program == "gecode":
        await cmake_git("Gecode/gecode", version)
        os.makedirs("/usr/local/share/minizinc/solvers", exist_ok=True)
        shutil.copy(
            "/usr/local/src/broccoli/provision/gecode.msc",
            "/usr/local/share/minizinc/solvers/gecode.msc",
        )
        installed[program] = version
    elif program == "minizinc":
        await cmake_git("MiniZinc/libminizinc", version)
        installed[program] = version
    else:
        raise ValueError(f"Unknown program '{program}'")
    return installed


# Really need to read into cancellation here...


async def do_while_reporting(task, send_status, status):
    while True:
        await send_status(status)
        try:
            await asyncio.wait_for(asyncio.shield(task), 10)
        except asyncio.TimeoutError:
            continue
        break
    assert task.done()
    if task.exception():
        raise task.exception()
    return task.result()


async def update_required_software(send_status):
    await send_status({"state": "updating apt packages"})
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
    installed = get_current_installed_versions()
    for program, version in target_installed:
        if program not in installed or installed[program] != version:
            installed = await do_while_reporting(
                asyncio.create_task(install(program, version, installed)),
                send_status=send_status,
                status={"state": f"installing {program} {version}"},
            )
            update_current_installed_versions(installed)
    await send_status({"state": "updates complete"})
