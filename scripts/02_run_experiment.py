# Runs one technique on one task on one model. Entry point: --task --technique --model --language
# Runs a single experiment. Usage: python scripts/02_run_experiment.py

from src.experiment_runner import run_experiment

print("Running experiment: cot + sentiment + english")
result = run_experiment(
    technique="cot",
    task="sentiment",
    language="english"
)

print("\n=== RESULTS ===")
for key, value in result.items():
    print(f"{key}: {value}")     
