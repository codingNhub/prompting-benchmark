# Orchestrates a single experiment run — one technique on one task on one model.

import os
import csv
import random
import ast
from datetime import datetime
from collections import Counter

from src.normaliser import normalise, parse_ner_entities, NORMALISER_VERSION
from src.config_manager import load_config
from src.dataset_loader import load_dataset
from src.prompt_manager import build_prompt, load_template
from src.model_wrapper import call_model
from src.metric_engine import compute_metrics
from src.logger import get_logger

logger = get_logger("experiment_runner")

PARSE_FAILURE_LABEL = "[PARSE_FAILURE]"


def run_experiment(technique: str, task: str, language: str = "english",
                   config_path: str = "configs/config.yaml") -> dict:

    logger.info(f"Starting experiment — technique={technique}, task={task}, language={language}")

    config = load_config(config_path)
    seed = config["experiment"]["random_seed"]
    random.seed(seed)

    model_key = config["models"]["active"]
    model_name = config["models"][model_key]

    examples = load_dataset(task, language)
    pool = examples
    test_examples = examples

    pred_path = f"outputs/predictions/{technique}_{task}_{language}.csv"
    completed_ids = set()
    raw_results = []

    if os.path.exists(pred_path):
        with open(pred_path, "r", encoding="utf-8") as f:
            done_rows = list(csv.DictReader(f))
            completed_ids = set(int(r["id"]) for r in done_rows)
            raw_results = done_rows
            logger.info(f"Resuming — {len(completed_ids)}/100 examples already done")

    test_examples = [e for e in test_examples if e["id"] not in completed_ids]

    if not test_examples:
        logger.info("All examples already completed — loading existing results")

    predictions = []
    references = []
    flagged_count = 0

    # Load previously completed predictions and references
    for r in raw_results:
        pred = r.get("prediction", "")
        ref = r.get("reference", "")
        if task in ("ner", "urdu_ner"):
            try:
                pred = ast.literal_eval(pred)
            except Exception:
                pred = []
            try:
                ref = ast.literal_eval(ref)
            except Exception:
                ref = []
        predictions.append(pred)
        references.append(ref)
        if r.get("status") != "ok":
            flagged_count += 1

    template = load_template(technique)
    valid_labels = template["tasks"][task].get("expected_labels", [])

    for example in test_examples:
        try:
            result = {}
            response = None
            input_tokens = 0
            output_tokens = 0
            prediction = None
            status = "failed"

            safe_pool = [e for e in pool if e["id"] != example["id"]]
            prompt = build_prompt(technique, task, example,
                                  few_shot_pool=safe_pool,
                                  example_id=example["id"], seed=seed)

            if technique == "self_consistency":
                n_samples = template["tasks"][task].get("n_samples", 3)
                sc_config = dict(config)
                sc_config["inference"] = dict(config.get("inference", {}))
                sc_config["inference"]["temperature_default"] = config.get(
                    "inference", {}).get("temperature_self_consistency", 0.7)

                ner_task = task in ("ner", "urdu_ner")
                votes = []
                entity_samples = []
                input_tokens_total = 0
                output_tokens_total = 0

                for _ in range(n_samples):
                    response = call_model(prompt, sc_config)
                    input_tokens_total += response["input_tokens"]
                    output_tokens_total += response["output_tokens"]
                    if ner_task:
                        tag_result = normalise(response["raw_text"])
                        result = tag_result
                        if tag_result["status"] == "ok":
                            entity_samples.append(set(parse_ner_entities(tag_result["label"])))
                    else:
                        result = normalise(response["raw_text"], valid_labels)
                        if result["status"] == "ok":
                            votes.append(result["label"])

                input_tokens = input_tokens_total / n_samples
                output_tokens = output_tokens_total / n_samples

                if ner_task:
                    entity_votes = Counter(e for sample in entity_samples for e in sample)
                    majority = n_samples // 2 + 1
                    prediction = [e for e, c in entity_votes.items() if c >= majority]
                    status = "ok" if prediction else "failed"
                    if status == "failed":
                        flagged_count += 1
                elif votes:
                    prediction = max(sorted(set(votes)), key=votes.count)
                    status = "ok"
                else:
                    prediction = PARSE_FAILURE_LABEL
                    status = "failed"
                    flagged_count += 1

            else:
                if task in ("summarisation", "qa"):
                    gen_budget = config.get("inference", {}).get("max_tokens_generation", 512)
                    response = call_model(prompt, config, max_tokens=gen_budget)
                else:
                    response = call_model(prompt, config)

                input_tokens = response["input_tokens"]
                output_tokens = response["output_tokens"]

                if task in ("ner", "urdu_ner"):
                    tag_result = normalise(response["raw_text"])
                    if tag_result["status"] == "ok":
                        entities = parse_ner_entities(tag_result["label"])
                        prediction = entities
                        status = "ok"
                    else:
                        prediction = []
                        status = "failed"
                        flagged_count += 1
                else:
                    result = normalise(response["raw_text"], valid_labels)
                    prediction = result["label"]
                    status = result["status"]
                    if status != "ok":
                        flagged_count += 1

            if prediction is None:
                prediction = PARSE_FAILURE_LABEL

            predictions.append(prediction)
            references.append(example["label"])

            new_row = {
                "id": example["id"],
                "text": example["text"][:100],
                "reference": example["label"],
                "prediction": str(prediction),
                "status": status,
                "failure_reason": result.get("reason", "") if isinstance(result, dict) else "",
                "raw_response": response["raw_text"] if response else "",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
            raw_results.append(new_row)

            os.makedirs("outputs/predictions", exist_ok=True)
            write_header = not os.path.exists(pred_path) or (len(completed_ids) == 0 and len(raw_results) == 1)
            with open(pred_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=new_row.keys())
                if write_header:
                    writer.writeheader()
                writer.writerow(new_row)

        except Exception as e:
            logger.error(f"Error on example {example['id']}: {e}")
            flagged_count += 1
            pred_val = [] if task in ("ner", "urdu_ner") else PARSE_FAILURE_LABEL
            predictions.append(pred_val)
            references.append(example["label"])

            err_row = {
                "id": example["id"],
                "text": example.get("text", "")[:100],
                "reference": example.get("label", ""),
                "prediction": str(pred_val),
                "status": "failed",
                "failure_reason": str(e),
                "raw_response": "",
                "input_tokens": 0,
                "output_tokens": 0
            }
            raw_results.append(err_row)

            os.makedirs("outputs/predictions", exist_ok=True)
            with open(pred_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=err_row.keys())
                writer.writerow(err_row)

    if not predictions:
        logger.error("No predictions — cannot compute metrics")
        return {}

    metrics = compute_metrics(task, predictions, references)

    token_inputs = [float(r["input_tokens"]) for r in raw_results if float(r.get("input_tokens", 0)) > 0]
    token_outputs = [float(r["output_tokens"]) for r in raw_results if float(r.get("output_tokens", 0)) > 0]
    avg_input = sum(token_inputs) / len(token_inputs) if token_inputs else 0
    avg_output = sum(token_outputs) / len(token_outputs) if token_outputs else 0

    result_row = {
        "experiment_id": f"{technique}_{task}_{language}_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "model": model_name,
        "technique": technique,
        "task": task,
        "language": language,
        "token_input_avg": round(avg_input, 1),
        "token_output_avg": round(avg_output, 1),
        "prompt_version": template["metadata"]["version"],
        "normaliser_version": NORMALISER_VERSION,
        "random_seed": seed,
        "flagged_count": flagged_count,
        "notes": ""
    }
    result_row.update(metrics)

    save_results(result_row)
    logger.info(f"Experiment complete — {technique}/{task} — metrics: {metrics}")
    return result_row


def save_results(result_row: dict):
    os.makedirs("outputs/results", exist_ok=True)
    path = "outputs/results/results_master.csv"

    all_columns = [
        "experiment_id", "date", "model", "technique", "task", "language",
        "token_input_avg", "token_output_avg", "prompt_version", "normaliser_version",
        "random_seed", "flagged_count", "notes",
        "macro_f1", "accuracy",
        "entity_f1", "precision", "recall",
        "rouge_l", "bert_f1",
        "exact_match", "token_f1"
    ]

    complete_row = {col: result_row.get(col, "") for col in all_columns}
    file_exists = os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_columns)
        if not file_exists:
            writer.writeheader()
        writer.writerow(complete_row)

    logger.info(f"Result saved to {path}")