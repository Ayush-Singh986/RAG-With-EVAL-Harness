# Source files

Every script here implements one stage of the RAG evaluation pipeline. Run scripts from the workspace root with `python src\<script>.py`.

| File | Goal / what it creates |
|---|---|
| `common.py` | Shared project paths, model names, JSON helpers, and text tokenizer. |
| `fetch_data.py` | Pins the upstream handbook revision, selects a deterministic subset, and copies Markdown into `data/raw/`. |
| `clean.py` | Removes front matter and markup noise, writes `data/clean/`, and generates `data/titles.json`. |
| `build_testset.py` | Checks source excerpts and calculates exact character offsets for reviewed questions. |
| `chunkers.py` | Implements fixed-size, heading-based, and semantic chunking with source offsets. |
| `index.py` | Embeds chunks and saves compressed NumPy vector indexes under `.cache/`. |
| `retrievers.py` | Implements vector, BM25, reciprocal-rank hybrid retrieval, and cross-encoder reranking. |
| `metrics.py` | Scores passage coverage, multi-passage recall, hit rate, and reciprocal rank. |
| `run_grid.py` | Measures all 24 chunker/search/reranker combinations on the dev set and writes `results/grid.csv`. |
| `run_headline.py` | Compares the four headline retrieval methods on the held-out main set. |
| `generate.py` | Calls configured answer/judge APIs and evaluates grounded answers; credentials come from local environment variables or `.env`. |
| `run_answers.py` | Saves per-question RAG answers or a separate no-retrieval control CSV. |
| `calibrate_threshold.py` | Measures the answerable/no-answer trade-off for reranker thresholds on dev questions. |
| `failures.py` | Exports missed dev questions and top retrieved evidence for manual diagnosis. |
| `ci_check.py` | Fails if a question that passed in the reviewed baseline regresses. |
| `plot_results.py` | Creates the README donut chart from actual RAG and control answer CSVs. |

Generated files are written to `data/`, `results/`, or `.cache/` as indicated; source inputs and measured outputs are not silently synthesized by these scripts.
