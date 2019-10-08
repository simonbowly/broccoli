import functools
import os
import shutil
import subprocess

import click

run = functools.partial(subprocess.check_call, shell=True)


@click.command()
@click.argument("commit")
def update(commit):
    run("git fetch", cwd="/usr/local/src/broccoli")
    run("git checkout master", cwd="/usr/local/src/broccoli")
    run(f"git reset --hard {commit}", cwd="/usr/local/src/broccoli")
    run("pip3 install /usr/local/src/broccoli --upgrade")
    shutil.copy(
        "/usr/local/src/broccoli/broccoli.service",
        "/etc/systemd/system/broccoli.service",
    )
    os.makedirs("/etc/broccoli", exist_ok=True)
    run(
        "git show | head -n 1 | sed 's|commit ||' > /etc/broccoli/githash",
        cwd="/usr/local/src/broccoli",
    )
    run("systemctl daemon-reload")
    run("systemctl enable broccoli")
    run("systemctl restart broccoli")
