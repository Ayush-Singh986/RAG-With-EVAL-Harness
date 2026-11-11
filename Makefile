.PHONY: data testset index grid answers control threshold failures chart test ci

data:
	python src/fetch_data.py
	python src/clean.py

testset:
	python src/build_testset.py

index:
	python src/index.py

grid:
	python src/run_grid.py

answers:
	python src/run_answers.py

control:
	python src/run_answers.py --control

threshold:
	python src/calibrate_threshold.py

failures:
	python src/failures.py

chart:
	python src/plot_results.py

test:
	pytest -q

ci:
	python src/ci_check.py --baseline results/baseline_perq.json
