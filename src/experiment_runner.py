

# Orchestrates a single experiment run — one technique on one task on one model.

import os
import csv
import time
import random
from datetime import datetime

from src.config_manager import load_config
from src.dataset_loader import load_dataset
from src.prompt_manager import build_prompt
from src.model_wrapper import call_model
from src.normaliser import normalise, normalise_ner
from src.metric_engine import compute_metrics
from src.logger import get_logger

logger = get_logger("experiment_runner")


def run_experiment(technique: str, task: str, language: str = "english",
                   config_path: str = "configs/config.yaml") -> dict:
    """
    Runs one complete experiment.
    Returns a dict with all results and metrics.
    """

    logger.info(f"Starting experiment — technique={technique}, task={task}, language={language}")

    # Load config and set seed
    config = load_config(config_path)
    seed = config["experiment"]["random_seed"]
    random.seed(seed)

    # Get model name
    model_key = config["models"]["active"]
    model_name = config["models"][model_key]

    # Load dataset
    examples = load_dataset(task, language)

    # For few-shot techniques — split into pool and test set
    # Use first 20 as pool, rest as test (never overlap)
    if technique in ("few_shot", "few_shot_cot"):
        pool = examples[:20]
        test_examples = examples[20:]
    else:
        pool = None
        test_examples = examples

    # Storage for predictions and references
    predictions = []
    references = []
    raw_results = []
    flagged_count = 0

    # Get valid labels from template
    from src.prompt_manager import load_template
    template = load_template(technique)
    valid_labels = template["tasks"][task].get("expected_labels", [])

    # Run each example
    for example in test_examples:
        try:
            # Build prompt
            prompt = build_prompt(technique, task, example, few_shot_pool=pool)

            # Handle self-consistency — run n times and take majority vote
            if technique == "self_consistency":
                n_samples = template["tasks"][task].get("n_samples", 3)
                sc_config = dict(config)
                sc_config["inference"] = dict(config.get("inference", {}))
                sc_config["inference"]["temperature_default"] = config.get(
                    "inference", {}).get("temperature_self_consistency", 0.7)

                votes = []
                for _ in range(n_samples):
                    response = call_model(prompt, sc_config)
                    result = normalise(response["raw_text"], valid_labels)
                    if result["status"] == "ok":
                        votes.append(result["label"])

                if votes:
                    # Majority vote
                    prediction = max(set(votes), key=votes.count)
                    status = "ok"
                else:
                    prediction = None
                    status = "failed"
                    flagged_count += 1

                input_tokens = 0
                output_tokens = 0

            else:
                # Standard single call
                response = call_model(prompt, config)
                input_tokens = response["input_tokens"]
                output_tokens = response["output_tokens"]

                # Normalise response
                if task in ("ner", "urdu_ner"):
                    entities = normalise_ner(response["raw_text"])
                    prediction = entities
                    status = "ok"
                else:
                    result = normalise(response["raw_text"], valid_labels)
                    prediction = result["label"]
                    status = result["status"]

                if status != "ok":
                    flagged_count += 1

            # Store results
            predictions.append(prediction)
            references.append(example["label"])

            raw_results.append({
                "id": example["id"],
                "text": example["text"][:100],
                "reference": example["label"],
                "prediction": str(prediction),
                "status": status,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            })

        except Exception as e:
            logger.error(f"Error on example {example['id']}: {e}")
            flagged_count += 1
            predictions.append(None)
            references.append(example["label"])

    # Filter out failed predictions before computing metrics
    valid_pairs = [(p, r) for p, r in zip(predictions, references) if p is not None]
    if not valid_pairs:
        logger.error("No valid predictions — cannot compute metrics")
        return {}

    valid_preds, valid_refs = zip(*valid_pairs)

    # Compute metrics
    metrics = compute_metrics(task, list(valid_preds), list(valid_refs))

    # Token averages
    token_inputs = [r["input_tokens"] for r in raw_results if r["input_tokens"] > 0]
    token_outputs = [r["output_tokens"] for r in raw_results if r["output_tokens"] > 0]
    avg_input = sum(token_inputs) / len(token_inputs) if token_inputs else 0
    avg_output = sum(token_outputs) / len(token_outputs) if token_outputs else 0

    # Build result row
    result_row = {
        "experiment_id": f"{technique}_{task}_{language}_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "model": model_name,
        "technique": technique,
        "task": task,
        "language": language,
        "token_input_avg": round(avg_input, 1),
        "token_output_avg": round(avg_output, 1),
        "prompt_version": "1.0",
        "random_seed": seed,
        "flagged_count": flagged_count,
        "notes": ""
    }
    result_row.update(metrics)

    # Save to results_master.csv
    save_results(result_row)

    logger.info(f"Experiment complete — {technique}/{task} — metrics: {metrics}")
    return result_row


def save_results(result_row: dict):
    """Appends one result row to results_master.csv."""

    os.makedirs("outputs/results", exist_ok=True)
    path = "outputs/results/results_master.csv"
    file_exists = os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=result_row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(result_row)

    logger.info(f"Result saved to {path}")