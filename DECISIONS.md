# Decisions and measured results

This file is intentionally a factual record of the experiments, not a place to invent benchmark results. Add measured values after preparing the handbook snapshot and reviewing the test questions.

## Decisions made so far

- Dataset: 515 cleaned Markdown files selected from the GitLab public handbook repository at commit `539e7d1d7e05c89dde7b20dfeb59ed968349c800`. The source pick was deterministic with seed 42. The handbook text itself does not have a clearly identified content-specific license in the repository root; confirm redistribution rights before publishing the cleaned corpus.
- Embeddings: `BAAI/bge-small-en-v1.5`; cosine similarity on normalized vectors, stored in a compressed NumPy matrix and ranked exactly. This keeps local builds portable on Windows without a C++ vector-database extension and is practical for this small corpus.
- Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- Chunkers: fixed 500/50, fixed 1000/100, heading-based, and semantic boundaries. The same cleaned-text offsets are retained for fair scoring.
- Hybrid retrieval: reciprocal rank fusion, because lexical and vector scores are not on a shared scale.
- CI: checks that previously passing answerable questions still pass; no model API keys are needed in CI.

## Measurements

- Corpus prepared: 515 cleaned files, about 6.0 MB of Markdown.
- Retrieval measurements: pending reviewed main/dev sets, package/model setup, index build, and evaluation. Do not treat the default `config/best.json` as experimentally selected until the dev grid has been evaluated.

## Limitations

- The 50-question main set requires human-written questions and exact passages copied from the committed cleaned handbook. It is not safe to synthesize its scores or passage offsets without that corpus.
- The public handbook may be present in an LLM's training data; include the no-retrieval control when interpreting answer quality.
- Small score differences may be sampling noise.
