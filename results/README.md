# Results

This folder is the destination for measured outputs; no benchmark scores are prefilled.

- `grid.csv`: dev-set experiment grid.
- `headline.csv`: main-set comparison of the headline methods.
- `answers_main.csv` and `answers_control.csv`: answer/judge outputs with and without retrieval.
- `answer_comparison.svg`: donut chart generated from the two answer CSVs with `python src\plot_results.py`.
- `failures.csv` and `thresholds.csv`: failure diagnosis and no-answer threshold measurements.
- `baseline_perq.json`: reviewed per-question CI baseline.

Only generated, measured results should be shown as project performance.
