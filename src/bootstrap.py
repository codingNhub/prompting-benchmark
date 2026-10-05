# Paired percentile bootstrap over the saved predictions: a 95% CI for each
# technique's primary metric, and for its difference from the task's best technique.
# Usage: python -m src.bootstrap   (writes outputs/tables/bootstrap_ci.csv)

import ast
import csv
import glob
import logging
import os

import numpy as np
from rouge_score import rouge_scorer
from sklearn.metrics import f1_score

from src.config_manager import load_config

LABELS = {"sentiment": ["Positive", "Negative", "Neutral"],
          "paraphrase": ["Paraphrase", "Not Paraphrase"]}
METRIC = {"sentiment": "macro_f1", "paraphrase": "macro_f1", "ner": "entity_f1",
          "qa": "exact_match", "summarisation": "rouge_l"}


def load_task(task):
    """Returns {technique: rows sorted by id} for every prediction file of a task."""
    out = {}
    for path in glob.glob(f"outputs/predictions/*_{task}_english.csv"):
        technique = os.path.basename(path)[:-len(f"_{task}_english.csv")]
        with open(path, encoding="utf-8") as f:
            out[technique] = sorted(csv.DictReader(f), key=lambda r: int(r["id"]))
    ids = {t: [r["id"] for r in rows] for t, rows in out.items()}
    assert len({tuple(v) for v in ids.values()}) == 1, f"{task}: techniques cover different example ids"
    return out


def scorer(task, rows):
    """Returns a function mapping an index array to the task's primary metric."""
    if task in LABELS:
        y = np.array([r["reference"] for r in rows])
        p = np.array([r["prediction"] for r in rows])
        return lambda idx: f1_score(y[idx], p[idx], average="macro", labels=LABELS[task], zero_division=0)
    if task == "ner":
        counts = []
        for r in rows:
            ref = set(ast.literal_eval(r["reference"]))
            pred = set(ast.literal_eval(r["prediction"])) if r["prediction"].startswith("[") else set()
            counts.append((len(pred & ref), len(pred - ref), len(ref - pred)))
        counts = np.array(counts)
        def ner_f1(idx):
            tp, fp, fn = counts[idx].sum(axis=0)
            return 2 * tp / (2 * tp + fp + fn) if tp else 0.0
        return ner_f1
    if task == "qa":
        from src.metric_engine import compute_qa, logger as metric_logger
        metric_logger.setLevel(logging.WARNING)
        per =np.array([compute_qa([r["prediction"]], [r["reference"]])["exact_match"] for r in rows])
    else:
        rs = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        per = np.array([rs.score(r["reference"], r["prediction"])["rougeL"].fmeasure for r in rows])
    return lambda idx: per[idx].mean()


def main():
    cfg = load_config()["bootstrap"]
    rng = np.random.default_rng(cfg["seed"])
    alpha = (1 - cfg["confidence_level"]) / 2 * 100
    out_rows = []
    for task, metric in METRIC.items():
        by_technique = load_task(task)
        fns = {t: scorer(task, rows) for t, rows in by_technique.items()}
        n = len(next(iter(by_technique.values())))
        full = np.arange(n)
        point = {t: fn(full) for t, fn in fns.items()}
        best = max(point, key=point.get)
        samples = rng.integers(0, n, size=(cfg["n_iterations"], n))
        boot = {t: np.array([fn(idx) for idx in samples]) for t, fn in fns.items()}
        for t in sorted(point, key=point.get, reverse=True):
            diff = boot[best] - boot[t]
            out_rows.append({
                "task": task, "technique": t, "metric": metric, "n": n,
                "point": round(point[t], 4),
                "ci_low": round(np.percentile(boot[t], alpha), 4),
                "ci_high": round(np.percentile(boot[t], 100 - alpha), 4),
                "best_technique": best,
                "diff_from_best": round(point[best] - point[t], 4),
                "diff_ci_low": round(np.percentile(diff, alpha), 4),
                "diff_ci_high": round(np.percentile(diff, 100 - alpha), 4),
                "best_significantly_better": bool(t != best and np.percentile(diff, alpha) > 0),
            })
    os.makedirs("outputs/tables", exist_ok=True)
    with open("outputs/tables/bootstrap_ci.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_rows[0].keys())
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Wrote {len(out_rows)} rows to outputs/tables/bootstrap_ci.csv")


if __name__ == "__main__":
    main()
