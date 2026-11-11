import json
import pathlib
import re

from common import ROOT

RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
FRONT = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
SHORTCODE = re.compile(r"\{\{[<%].*?[%>]\}\}", re.S)
COMMENT = re.compile(r"<!--.*?-->", re.S)


def clean(text: str) -> str:
    text = COMMENT.sub("", SHORTCODE.sub("", text))
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def main() -> int:
    if not RAW.is_dir() or not any(RAW.glob("*.md")):
        raise FileNotFoundError(f"No raw Markdown documents found in {RAW}; run fetch_data.py first")
    CLEAN.mkdir(parents=True, exist_ok=True)
    titles: dict[str, str] = {}
    for path in sorted(RAW.glob("*.md")):
        raw = path.read_text(encoding="utf-8", errors="replace")
        match = FRONT.match(raw)
        title = ""
        if match:
            title_match = re.search(r"^title:\s*(.+)$", match.group(1), re.M)
            title = title_match.group(1).strip().strip("\"'") if title_match else ""
            raw = raw[match.end():]
        text = clean(raw)
        if len(text) < 800:
            continue
        (CLEAN / path.name).write_text(text, encoding="utf-8", newline="\n")
        titles[path.name] = title or path.stem.split("__")[-1].replace("-", " ")

    for old in CLEAN.glob("*.md"):
        if old.name not in titles:
            old.unlink()
    (ROOT / "data" / "titles.json").write_text(
        json.dumps(titles, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Cleaned {len(titles)} files")
    return len(titles)


if __name__ == "__main__":
    main()
