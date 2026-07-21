# Reruns a single failed example and updates the predictions CSV.
# Usage: python scripts/rerun_example.py --technique zero_shot --task ner --language english --id 89

import argparse
import csv
import os
import random

from src.config_manager import load_config
from src.dataset_loader import load_dataset
from src.prompt_manager import build_prompt, load_template
from src.model_wrapper import call_model
from src.normaliser import normalise, parse_ner_entities
from src.metric_engine import compute_metrics
from src.experiment_runner import save_results, PARSE_FAILURE_LABEL
from src.normaliser import NORMALISER_VERSION
from src.logger import get_logger
from datetime import datetime

logger = get_logger("rerun_example")


def rerun_example(technique, task, language, example_id):
    config = load_config()
    seed = config["experiment"]["random_seed"]
    random.seed(seed)

    examples = load_dataset(task, language)
    example = next((e for e in examples if e["id"] == example_id), None)

    if example is None:
        print(f"Example ID {example_id} not found in dataset.")
        return

    template = load_template(technique)
    valid_labels = template["tasks"][task].get("expected_labels", [])

    safe_pool = [e for e in examples if e["id"] != example["id"]]
    prompt = build_prompt(technique, task, example,
                          few_shot_pool=safe_pool,
                          example_id=example["id"], seed=seed)

    if task in ("summarisation", "qa"):
        gen_budget = config.get("inference", {}).get("max_tokens_generation", 512)
        response = call_model(prompt, config, max_tokens=gen_budget)
    else:
        response = call_model(prompt, config)

    if task in ("ner", "urdu_ner"):
        tag_result = normalise(response["raw_text"])
        if tag_result["status"] == "ok":
            prediction = parse_ner_entities(tag_result["label"])
            status = "ok"
        else:
            prediction = []
            status = "failed"
        result = tag_result
    else:
        result = normalise(response["raw_text"], valid_labels)
        prediction = result["label"] or PARSE_FAILURE_LABEL
        status = result["status"]

    new_row = {
        "id": example["id"],
        "text": example["text"][:100],
        "reference": example["label"],
        "prediction": str(prediction),
        "status": status,
        "failure_reason": result.get("reason", ""),
        "raw_response": response["raw_text"],
        "input_tokens": response["input_tokens"],
        "output_tokens": response["output_tokens"]
    }

    print(f"Result: status={status} prediction={str(prediction)[:80]}")

    # Update the predictions CSV — replace the old row for this ID
    pred_path = f"outputs/predictions/{technique}_{task}_{language}.csv"

    if not os.path.exists(pred_path):
        print(f"Predictions file not found: {pred_path}")
        return

    with open(pred_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Replace the row with matching ID
    updated = False
    for i, row in enumerate(rows):
        if int(row["id"]) == example_id:
            rows[i] = new_row
            updated = True
            break

    if not updated:
        rows.append(new_row)
        print(f"ID {example_id} was not in file — appended as new row.")

    # Write back the full CSV
    with open(pred_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=new_row.keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {pred_path}")

    # Recompute metrics from the full updated CSV
    with open(pred_path, encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))

    import ast
    all_preds = []
    all_refs = []
    for r in all_rows:
        ref = r["reference"]
        pred = r["prediction"]
        if task in ("ner", "urdu_ner"):
            try:
                pred = ast.literal_eval(pred)
                ref = ast.literal_eval(ref)
            except:
                pred = []
        all_preds.append(pred)
        all_refs.append(ref)

    metrics = compute_metrics(task, all_preds, all_refs)
    flagged = sum(1 for r in all_rows if r["status"] != "ok")

    print(f"\nRecomputed metrics after fix:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    print(f"  flagged_count: {flagged}")

    # Save updated result to results_master.csv
    model_key = config["models"]["active"]
    model_name = config["models"][model_key]

    result_row = {
        "experiment_id": f"{technique}_{task}_{language}_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "model": model_name,
        "technique": technique,
        "task": task,
        "language": language,
        "token_input_avg": 0,
        "token_output_avg": 0,
        "prompt_version": template["metadata"]["version"],
        "normaliser_version": NORMALISER_VERSION,
        "random_seed": seed,
        "flagged_count": flagged,
        "notes": f"rerun of example {example_id}"
    }
   # Update results_master.csv — replace existing row
    results_path = "outputs/results/results_master.csv"
    if os.path.exists(results_path):
        with open(results_path, encoding="utf-8") as f:
            all_results = list(csv.DictReader(f))
        all_results = [r for r in all_results
                      if not (r["technique"] == technique and
                              r["task"] == task and
                              r["language"] == language)]
        all_results.append(result_row)
        with open(results_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(result_row.keys()))
            writer.writeheader()
            writer.writerows(all_results)
        print(f"Updated results_master.csv")
    else:
        save_results(result_row)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--technique", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--language", default="english")
    parser.add_argument("--id", type=int, required=True)
    args = parser.parse_args()

    rerun_example(args.technique, args.task, args.language, args.id)