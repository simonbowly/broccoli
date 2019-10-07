from hashlib import md5
from os import makedirs, remove
from pathlib import Path
from shutil import copy
from subprocess import check_call
from sys import argv

run = check_call


def apt_update():
    run(["apt-get", "update"])


def apt_install(*packages):
    run(["apt-get", "install", "-y"] + list(packages))


def git_checkout(repo_url, commit="master"):
    base = Path(".")
    _, _, name = repo_url.rpartition("/")
    target = base / name.replace(".git", "")
    if not target.exists():
        run(["git", "clone", repo_url], cwd=base)
    run(["git", "checkout", commit], cwd=target)
    return target


def download_file(package_dir, file_url, md5hash):
    base_path, sep, file_name = file_url.rpartition("/")
    local_path = package_dir / file_name
    if local_path.exists():
        md5sum = md5(local_path.read_bytes())
        if md5sum.hexdigest() == md5hash:
            return local_path
        remove(local_path)
    run(["wget", file_url], cwd=package_dir)
    md5sum = md5(local_path.read_bytes())
    assert md5sum.hexdigest() == md5hash
    return local_path


def wget_extract_tar(file_url, md5hash):
    base = Path(".")
    archive = download_file(base, file_url, md5hash)
    run(["tar", "xf", archive], cwd=base)
    return archive.parent / archive.stem.replace(".tar", "")


def cmake(path, install=True, release=True, flags=None):
    build_dir = path / "build"
    makedirs(build_dir, exist_ok=True)
    cmd = ["cmake", ".."]
    if release:
        cmd.append("-DCMAKE_BUILD_TYPE=Release")
    if flags:
        cmd.extend(flags)
    run(cmd, cwd=build_dir)
    run(["cmake", "--build", ".", "--clean-first", "-j", "4"], cwd=build_dir)
    if install:
        run(["cmake", "--build", ".", "--target", "install"], cwd=build_dir)


def configure_make(build_dir, install=True):
    run(["./configure"], cwd=build_dir)
    run(["make"], cwd=build_dir)
    if install:
        run(["make", "install"], cwd=build_dir)


if __name__ == "__main__":

    host = argv[1]
    here = Path(__file__).parent

    apt_update()
    apt_install(
        "bison",
        "build-essential",
        "cmake",
        "flex",
        "git",
        "libgmp-dev",
        "libgsl-dev",
        "libreadline-dev",
        "libxml2-dev",
        "man-db",
        "nano",
        "pkg-config",
        "python3-dev",
        "python3-pip",
        "stress",
        "ufw",
        "wget",
        "zlib1g-dev",
    )

    run(["pip3", "install", "pip", "--upgrade"])
    run(["pip", "install", "-r", f"{here}/requirements.txt"])

    # Development libraries
    cmake(git_checkout(f"git@{host}:emil-e/rapidcheck", "d9482c6"))
    configure_make(
        wget_extract_tar(
            f"http://{host}/source/igraph-0.7.1.tar.gz",
            md5hash="4f6e7c16b45fce8ed423516a9786e4e8",
        )
    )

    # Optimisers
    cmake(git_checkout(f"git@{host}:chuffed/chuffed", "0.10.4"))
    cmake(git_checkout(f"git@{host}:Gecode/gecode", "release-6.2.0"))
    cmake(
        wget_extract_tar(
            f"http://{host}/source/scipoptsuite-6.0.2.tgz",
            md5hash="6b2b6cacc43ba6776cc5018edabb0cc4",
        )
    )

    # Minizinc (needs MIP solvers installed before build)
    cmake(
        git_checkout(f"git@{host}:MiniZinc/libminizinc", "2.3.2"),
        flags=["-DUSE_PROPRIETARY=on"],
    )
    makedirs("/usr/local/share/minizinc/solvers")
    for solver in ["chuffed", "gecode"]:
        copy(here / f"{solver}.msc", f"/usr/local/share/minizinc/solvers/{solver}.msc")

    # Install the tasks service
    copy(here / "../tasks/task-subscriber.py", f"/usr/local/bin/task-subscriber.py")
    copy(
        here / "../tasks/task-subscriber.service",
        "/etc/systemd/system/task-subscriber.service",
    )
    run(["systemctl", "daemon-reload"])
    run(["systemctl", "enable", "task-subscriber"])
    run(["systemctl", "restart", "task-subscriber"])
