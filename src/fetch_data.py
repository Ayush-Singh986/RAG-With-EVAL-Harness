import pathlib
import random
import shutil
import subprocess

from common import ROOT

REPO = "https://gitlab.com/gitlab-com/content-sites/handbook.git"
FULL = ROOT / "data" / "handbook_full"
RAW = ROOT / "data" / "raw"
VERSION = ROOT / "data" / "DATA_VERSION.txt"
HR_HINTS = (
    "people-group", "total-rewards", "benefits", "leave", "time-off",
    "onboarding", "expense", "travel", "conduct", "harassment", "compensation",
)


def run(*cmd: str, cwd: pathlib.Path | None = None) -> str:
    result = subprocess.run(
        cmd, cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8"
    )
    return result.stdout.strip()


def fetch() -> None:
    FULL.parent.mkdir(parents=True, exist_ok=True)
    if VERSION.exists():
        commit = VERSION.read_text(encoding="utf-8").strip()
        if not commit:
            raise ValueError(f"{VERSION} is empty")
        FULL.mkdir(parents=True, exist_ok=True)
        if not (FULL / ".git").exists():
            run("git", "init", cwd=FULL)
            run("git", "remote", "add", "origin", REPO, cwd=FULL)
        run("git", "fetch", "--depth", "1", "origin", commit, cwd=FULL)
        run("git", "checkout", "--detach", "FETCH_HEAD", cwd=FULL)
    else:
        if FULL.exists():
            raise FileExistsError(
                f"{FULL} exists without {VERSION}; move it aside or remove it explicitly."
            )
        run("git", "clone", "--depth", "1", REPO, str(FULL))
        commit = run("git", "rev-parse", "HEAD", cwd=FULL)
        VERSION.write_text(commit + "\n", encoding="utf-8")


def pick() -> int:
    files = [
        path for path in sorted(FULL.rglob("*.md"))
        if 1500 < path.stat().st_size < 60000 and ".git" not in path.parts
    ]
    hr = [path for path in files if any(hint in str(path).lower() for hint in HR_HINTS)]
    hr_set = set(hr)
    rest = [path for path in files if path not in hr_set]
    random.seed(42)
    chosen = random.sample(hr, min(250, len(hr))) + random.sample(rest, min(350, len(rest)))
    if not chosen:
        raise RuntimeError(f"No eligible Markdown files found under {FULL}")
    RAW.mkdir(parents=True, exist_ok=True)
    for existing in RAW.glob("*.md"):
        existing.unlink()
    for path in chosen:
        flat = str(path.relative_to(FULL)).replace("\\", "__").replace("/", "__")
        shutil.copy2(path, RAW / flat)
    print(f"Copied {len(chosen)} files ({len(hr)} HR candidates, {len(rest)} others available)")
    return len(chosen)


if __name__ == "__main__":
    fetch()
    pick()
