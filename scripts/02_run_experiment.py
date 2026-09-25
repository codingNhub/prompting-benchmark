# Runs a single experiment. No CLI args — edit technique/task/language below and rerun per combination.
# Usage: python scripts/02_run_experiment.py

from src.experiment_runner import run_experiment

technique = "cot"
task = "summarisation"
language = "english"

print(f"Running experiment: {technique} + {task} + {language}")
result = run_experiment(
    technique=technique,
    task=task,
    language=language
)

print("\n=== RESULTS ===")
for key, value in result.items():
    print(f"{key}: {value}")     
