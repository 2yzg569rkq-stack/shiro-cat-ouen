#!/usr/bin/env python3
"""Regenerate the site and publish content changes from this Mac."""

import fcntl
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parent
CSV = Path.home() / "TapoHourlyXPipeline/data/lost_cat_reposts.csv"
INDEX = Path("docs/index.html")
UPDATED = re.compile(rb"(?m)^  " + "最終更新：".encode() + rb"[0-9][^\r\n]*(?=<br>$)")


def git(*args, **kwargs):
    return subprocess.run(
        ["/usr/bin/git", *args], cwd=REPO, check=True, **kwargs
    ).stdout


def log(message):
    print(f"[{datetime.now().astimezone().isoformat(timespec='seconds')}] {message}", flush=True)


def update():
    if git("branch", "--show-current", capture_output=True).strip() != b"main":
        raise RuntimeError("The checkout must be on main.")
    if git("status", "--porcelain", "--", str(INDEX), capture_output=True):
        raise RuntimeError(f"Commit or restore existing edits to {INDEX} before updating.")

    committed = git("show", f"HEAD:{INDEX}", capture_output=True)
    with TemporaryDirectory(prefix="shiro-cat-build-", dir=REPO / ".git") as temp:
        subprocess.run(
            [sys.executable, "build_site.py", str(CSV), temp], cwd=REPO, check=True
        )
        generated = Path(temp) / INDEX.name
        if UPDATED.sub(b"", generated.read_bytes()) == UPDATED.sub(b"", committed):
            log("Page content is unchanged.")
        else:
            generated.replace(REPO / INDEX)
            try:
                git("commit", "-m", "Update cat support listings", "--", str(INDEX))
            except subprocess.CalledProcessError:
                git("restore", "--worktree", "--", str(INDEX))
                raise

    if git("rev-list", "origin/main..HEAD", capture_output=True).strip():
        git("push", "origin", "main")
        log("Pushed page updates.")


if __name__ == "__main__":
    with (REPO / ".git/shiro-cat-update.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        log("Checking for listing updates.")
        update()
