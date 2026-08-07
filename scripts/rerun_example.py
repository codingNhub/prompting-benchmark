# Reruns a single failed example and updates the predictions CSV.
# Usage: python -m scripts.rerun_example --technique zero_shot --task ner --language english --id 89

import argparse
import csv
import os
import ast
import random
from datetime import datetime

from src.config_manager import load_config
from src.dataset_loader import load_dataset
from src.prompt_manager import build_prompt, load_template
from src.model_wrapper import call_model
from src.normaliser import normalise, parse_ner_entities, NORMALISER_VERSION
from src.metric_engine import compute_metrics
from src.experiment_runner import PARSE_FAILURE_LABEL
from src.logger import get_logger

logger = get_logger("rerun_example")


def rerun_example(technique, task, language, example_id):
    technique = technique.lower()
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
        gen_config = dict(config)
        gen_config["inference"] = dict(config.get("inference", {}))
        gen_config["inference"].setdefault("reasoning_effort", "low")
        response = call_model(prompt, gen_config, max_tokens=gen_budget)
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
        "reference": str(example["label"]),
        "prediction": str(prediction),
        "status": status,
        "failure_reason": result.get("reason", ""),
        "raw_response": response["raw_text"],
        "input_tokens": response["input_tokens"],
        "output_tokens": response["output_tokens"]
    }

    print(f"Result: status={status} prediction={str(prediction)[:80]}")

    # ── Update predictions CSV ────────────────────────────────
    pred_path = f"outputs/predictions/{technique}_{task}_{language}.csv"
    if not os.path.exists(pred_path):
        print(f"Predictions file not found: {pred_path}")
        return

    with open(pred_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        pred_fieldnames = reader.fieldnames
        rows = list(reader)

    # ── FIX 2: Guard against re-running passing examples ─────
    current = next((r for r in rows if int(r["id"]) == example_id), None)
    if current and current.get("status") == "ok":
        print(f"WARNING: Example {example_id} already has status=ok")
        print(f"Current prediction: {current.get('prediction')}")
        confirm = input("Re-run a passing example? Type YES to continue: ")
        if confirm.strip() != "YES":
            print("Aborted.")
            return

    updated = False
    for i, row in enumerate(rows):
        if int(row["id"]) == example_id:
            merged = dict(row)
            merged.update(new_row)
            rows[i] = merged
            updated = True
            break

    if not updated:
        rows.append(new_row)
        print(f"ID {example_id} was not in file — appended.")

    with open(pred_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=pred_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {pred_path}")

    # ── Recompute metrics ─────────────────────────────────────
    with open(pred_path, encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))

    all_preds, all_refs = [], []
    for r in all_rows:
        pred = r["prediction"]
        ref = r["reference"]
        if task in ("ner", "urdu_ner"):
            try:
                pred = ast.literal_eval(pred)
                ref = ast.literal_eval(ref)
            except:
                pred = []
        all_preds.append(pred)
        all_refs.append(ref)

    metrics = compute_metrics(task, all_preds, all_refs)
    flagged = sum(1 for r in all_rows if r.get("status") != "ok")

    print(f"\nRecomputed metrics after fix:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    print(f"  flagged_count: {flagged}")

    # ── FIX 3: Permanent rerun log ────────────────────────────
    log_path = "outputs/rerun_log.csv"
    log_exists = os.path.exists(log_path)
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "technique", "task", "language", "example_id",
            "before_status", "before_prediction", "after_status", "after_prediction"
        ])
        if not log_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "technique": technique,
            "task": task,
            "language": language,
            "example_id": example_id,
            "before_status": current.get("status", "unknown") if current else "not_found",
            "before_prediction": current.get("prediction", "") if current else "",
            "after_status": status,
            "after_prediction": str(prediction)
        })
    print(f"Rerun logged to {log_path}")

    # ── Update results_master.csv safely ──────────────────────
    results_path = "outputs/results/results_master.csv"
    model_key = config["models"]["active"]
    model_name = config["models"][model_key]

    # Compute token averages from full predictions file
    tokens_in = [float(r["input_tokens"]) for r in all_rows
                 if r.get("input_tokens", "0") not in ("0", "")]
    tokens_out = [float(r["output_tokens"]) for r in all_rows
                  if r.get("output_tokens", "0") not in ("0", "")]

    new_result = {
        "experiment_id": f"{technique}_{task}_{language}_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "model": model_name,
        "technique": technique,
        "task": task,
        "language": language,
        "token_input_avg": round(sum(tokens_in)/len(tokens_in), 1) if tokens_in else "",
        "token_output_avg": round(sum(tokens_out)/len(tokens_out), 1) if tokens_out else "",
        "prompt_version": template["metadata"]["version"],
        "normaliser_version": NORMALISER_VERSION,
        "random_seed": seed,
        "flagged_count": flagged,
        "notes": f"rerun of example {example_id}"
    }
    new_result.update(metrics)

    if os.path.exists(results_path):
        with open(results_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_fieldnames = list(reader.fieldnames)
            all_results = list(reader)

        all_results = [r for r in all_results
                       if not (r.get("technique") == technique and
                               r.get("task") == task and
                               r.get("language") == language)]

        safe_row = {col: new_result.get(col, "") for col in existing_fieldnames}
        all_results.append(safe_row)

        with open(results_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=existing_fieldnames)
            writer.writeheader()
            writer.writerows(all_results)

        print(f"Updated results_master.csv — {len(all_results)} total rows")
    else:
        from src.experiment_runner import save_results
        save_results(new_result)

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--technique", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--language", default="english")
    parser.add_argument("--id", type=int, required=True)
    args = parser.parse_args()

    rerun_example(args.technique, args.task, args.language, args.id)