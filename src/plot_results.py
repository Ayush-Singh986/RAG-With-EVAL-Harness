import argparse
import csv
import html
from pathlib import Path

from common import ROOT

COLORS = {"correct": "#16856b", "incorrect": "#d9e2e8"}
WIDTH, HEIGHT = 760, 400


def read_answers(path: Path) -> dict[str, bool]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not {"id", "correct"} <= set(reader.fieldnames):
            raise ValueError(f"{path} must have id and correct columns")
        answers: dict[str, bool] = {}
        for line, row in enumerate(reader, start=2):
            qid = (row.get("id") or "").strip()
            raw = (row.get("correct") or "").strip().lower()
            if not qid or qid in answers:
                raise ValueError(f"{path}:{line} has a missing or duplicate question id")
            if raw not in {"true", "false"}:
                raise ValueError(f"{path}:{line} has invalid correct value {raw!r}")
            answers[qid] = raw == "true"
    if not answers:
        raise ValueError(f"{path} has no answer rows")
    return answers


def _donut(cx: int, cy: int, radius: int, correct: int, total: int, label: str) -> str:
    rate = correct / total if total else 0
    circumference = 2 * 3.141592653589793 * radius
    correct_length = circumference * rate
    percent = round(rate * 100)
    safe_label = html.escape(label)
    return f"""
  <g role="img" aria-label="{safe_label}: {correct} correct out of {total}, {percent} percent">
    <circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{COLORS['incorrect']}" stroke-width="24"/>
    <circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{COLORS['correct']}" stroke-width="24"
      stroke-dasharray="{correct_length:.2f} {circumference:.2f}" transform="rotate(-90 {cx} {cy})"/>
    <text x="{cx}" y="{cy - 2}" text-anchor="middle" class="score">{percent}%</text>
    <text x="{cx}" y="{cy + 25}" text-anchor="middle" class="detail">{correct}/{total} correct</text>
    <text x="{cx}" y="{cy + radius + 53}" text-anchor="middle" class="label">{safe_label}</text>
  </g>"""


def build_svg(rag: dict[str, bool], control: dict[str, bool]) -> str:
    if set(rag) != set(control):
        raise ValueError("RAG and control CSVs must contain the same question IDs")
    total = len(rag)
    rag_correct = sum(rag.values())
    control_correct = sum(control.values())
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title description">
  <title id="title">RAG answer quality compared with no-retrieval control</title>
  <desc id="description">Correct answers are shown in green and incorrect answers in gray across {total} questions. RAG: {rag_correct} correct. No retrieval: {control_correct} correct.</desc>
  <style>
    text {{ font-family: Inter, Segoe UI, sans-serif; fill: #17313b; }}
    .heading {{ font-size: 21px; font-weight: 650; }}
    .score {{ font-size: 35px; font-weight: 700; }}
    .detail {{ font-size: 13px; fill: #536871; }}
    .label {{ font-size: 16px; font-weight: 600; }}
    .legend {{ font-size: 13px; fill: #536871; }}
  </style>
  <rect width="100%" height="100%" rx="18" fill="#ffffff"/>
  <text x="{WIDTH / 2:.0f}" y="38" text-anchor="middle" class="heading">Measured answer quality · {total} questions</text>
  {_donut(220, 190, 82, rag_correct, total, "With retrieval")}
  {_donut(540, 190, 82, control_correct, total, "No-retrieval control")}
  <circle cx="274" cy="370" r="6" fill="{COLORS['correct']}"/>
  <text x="286" y="375" class="legend">Correct</text>
  <circle cx="380" cy="370" r="6" fill="{COLORS['incorrect']}"/>
  <text x="392" y="375" class="legend">Incorrect</text>
</svg>
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an SVG donut chart from the measured RAG/control answer CSVs."
    )
    parser.add_argument("--rag", type=Path, default=ROOT / "results" / "answers_main.csv")
    parser.add_argument("--control", type=Path, default=ROOT / "results" / "answers_control.csv")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "results" / "answer_comparison.svg"
    )
    args = parser.parse_args()
    rag_answers = read_answers(args.rag)
    control_answers = read_answers(args.control)
    svg = build_svg(rag_answers, control_answers)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8", newline="\n")
    print(f"Saved measured RAG/control donut chart to {args.output}")


if __name__ == "__main__":
    main()
