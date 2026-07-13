# Computes task-appropriate evaluation metrics: F1, accuracy, ROUGE-L, BERTScore, exact match.
# Computes evaluation metrics for all 5 task types.

from src.logger import get_logger

logger = get_logger("metric_engine")


def compute_sentiment(predictions: list, references: list) -> dict:
    """Macro F1 for 3-class sentiment classification."""
    from sklearn.metrics import f1_score, accuracy_score

    f1 = f1_score(references, predictions, average="macro", zero_division=0)
    acc = accuracy_score(references, predictions)

    logger.info(f"Sentiment — macro_f1={f1:.4f}, accuracy={acc:.4f}")
    return {"macro_f1": round(f1, 4), "accuracy": round(acc, 4)}


def compute_paraphrase(predictions: list, references: list) -> dict:
    """Macro F1 for binary paraphrase classification."""
    from sklearn.metrics import f1_score, accuracy_score

    f1 = f1_score(references, predictions, average="macro", zero_division=0)
    acc = accuracy_score(references, predictions)

    logger.info(f"Paraphrase — macro_f1={f1:.4f}, accuracy={acc:.4f}")
    return {"macro_f1": round(f1, 4), "accuracy": round(acc, 4)}


def compute_ner(predictions: list, references: list) -> dict:
    """
    Entity-level F1 for NER.
    predictions and references are lists of lists of (entity, type) tuples.
    """
    true_pos = 0
    false_pos = 0
    false_neg = 0

    for pred_entities, ref_entities in zip(predictions, references):
        pred_set = set(pred_entities)
        ref_set = set(ref_entities)

        true_pos += len(pred_set & ref_set)
        false_pos += len(pred_set - ref_set)
        false_neg += len(ref_set - pred_set)

    precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) > 0 else 0
    recall = true_pos / (true_pos + false_neg) if (true_pos + false_neg) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    logger.info(f"NER — entity_f1={f1:.4f}, precision={precision:.4f}, recall={recall:.4f}")
    return {
        "entity_f1": round(f1, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4)
    }


def compute_summarisation(predictions: list, references: list) -> dict:
    """ROUGE-L and BERTScore for summarisation."""
    from rouge_score import rouge_scorer
    import bert_score

    # ROUGE-L
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    rouge_scores = [scorer.score(ref, pred)["rougeL"].fmeasure
                    for pred, ref in zip(predictions, references)]
    rouge_l = sum(rouge_scores) / len(rouge_scores)

    # BERTScore
    P, R, F = bert_score.score(
        predictions, references,
        model_type="bert-base-uncased",
        rescale_with_baseline=True,
        verbose=False
    )
    bert_f1 = F.mean().item()

    logger.info(f"Summarisation — rouge_l={rouge_l:.4f}, bert_f1={bert_f1:.4f}")
    return {
        "rouge_l": round(rouge_l, 4),
        "bert_f1": round(bert_f1, 4)
    }


def compute_qa(predictions: list, references: list) -> dict:
    """Exact match and token-level F1 for QA."""

    import re
    import string

    def normalize(text):
        text = text.lower()
        text = re.sub(r"\b(a|an|the)\b", " ", text)
        text = "".join(ch for ch in text if ch not in string.punctuation)
        return " ".join(text.split())

    def token_f1(pred, ref):
        pred_tokens = normalize(pred).split()
        ref_tokens = normalize(ref).split()
        common = set(pred_tokens) & set(ref_tokens)
        if not common:
            return 0.0
        precision = len(common) / len(pred_tokens)
        recall = len(common) / len(ref_tokens)
        return 2 * precision * recall / (precision + recall)

    exact_matches = [
        1 if normalize(p) == normalize(r) else 0
        for p, r in zip(predictions, references)
    ]
    token_f1s = [token_f1(p, r) for p, r in zip(predictions, references)]

    em = sum(exact_matches) / len(exact_matches)
    f1 = sum(token_f1s) / len(token_f1s)

    logger.info(f"QA — exact_match={em:.4f}, token_f1={f1:.4f}")
    return {"exact_match": round(em, 4), "token_f1": round(f1, 4)}


def compute_metrics(task: str, predictions: list, references: list) -> dict:
    """
    Router function — calls the correct metric function for the task.
    """
    if task in ("sentiment", "urdu_sentiment"):
        return compute_sentiment(predictions, references)
    elif task in ("ner", "urdu_ner"):
        return compute_ner(predictions, references)
    elif task == "summarisation":
        return compute_summarisation(predictions, references)
    elif task == "qa":
        return compute_qa(predictions, references)
    elif task == "paraphrase":
        return compute_paraphrase(predictions, references)
    else:
        raise ValueError(f"Unknown task: {task}")