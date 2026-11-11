import json
import os
import time
import urllib.error
import urllib.request

from dotenv import load_dotenv

from common import ROOT

load_dotenv(ROOT / ".env")

SYSTEM = (
    "Answer using ONLY the context below. If the context does not contain the answer, "
    "reply exactly: Not found in documents. Name the source file you used."
)
NOT_FOUND = "Not found in documents."


def call_llm(prompt: str, system: str | None = None, role: str = "ANSWER") -> str:
    prefix = f"RAG_{role}_"
    api_key = os.environ.get(prefix + "API_KEY")
    model = os.environ.get(prefix + "MODEL")
    base_url = os.environ.get(prefix + "BASE_URL", "https://api.openai.com/v1").rstrip("/")
    if not api_key or not model:
        raise RuntimeError(f"Set {prefix}API_KEY and {prefix}MODEL to call the {role.lower()} model")
    payload = json.dumps({
        "model": model,
        "temperature": 0,
        "messages": ([{"role": "system", "content": system}] if system else [])
        + [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    request = urllib.request.Request(
        base_url + "/chat/completions", data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{role.title()} model request failed: {exc}") from exc
    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected {role.lower()} API response shape") from exc
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(f"{role.title()} model returned an empty answer")
    return content.strip()


def answer(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[source: {chunk['file']}]\n{chunk['text']}" for chunk in chunks
    )
    return call_llm(f"Context:\n{context}\n\nQuestion: {question}", system=SYSTEM)


def answer_no_retrieval(question: str) -> str:
    return call_llm(
        f"Question about the GitLab handbook: {question}\n"
        "If you do not know, reply exactly: Not found in documents.",
        system="Answer the question accurately. Do not invent details.",
    )


def judge(question: str, expected: str, response: str, chunks: list[dict]) -> dict:
    answer_model = os.environ.get("RAG_ANSWER_MODEL")
    judge_model = os.environ.get("RAG_JUDGE_MODEL")
    if answer_model and judge_model and answer_model == judge_model:
        raise ValueError("RAG_ANSWER_MODEL and RAG_JUDGE_MODEL must be different")
    context = "\n".join(chunk["text"] for chunk in chunks)
    prompt = f"""You are grading an answer.
Question: {question}
Correct answer: {expected}
Model answer: {response}
Context given to the model:
{context}

Return only JSON: {{"correct": true/false, "faithful": true/false}}
correct = matches the correct answer in meaning.
faithful = every claim in the model answer is supported by the context."""
    raw = call_llm(prompt, role="JUDGE")
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Judge returned invalid JSON: {raw!r}") from exc
    if not isinstance(result, dict) or not isinstance(result.get("correct"), bool) or not isinstance(result.get("faithful"), bool):
        raise ValueError(f"Judge response must contain boolean correct and faithful fields: {raw!r}")
    return result


def evaluate(question: dict, chunks: list[dict], control: bool = False) -> dict:
    start = time.perf_counter()
    response = answer_no_retrieval(question["question"]) if control else answer(
        question["question"], chunks
    )
    latency_ms = round(1000 * (time.perf_counter() - start))
    if question["type"] == "no_answer":
        verdict = {
            "correct": "not found" in response.lower(),
            "faithful": "not found" in response.lower(),
        }
    else:
        verdict = judge(
            question["question"], question["expected_answer"], response, chunks
        )
    return {"answer": response, **verdict, "latency_ms": latency_ms}
