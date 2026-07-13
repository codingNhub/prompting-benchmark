import os
import ast
import pandas as pd
from src.logger import get_logger

logger = get_logger("dataset_loader")

# Fine-grained MultiNERD types collapse onto the 4 coarse types the prompts use.
_COARSE_TYPE = {"PER": "PERSON", "ORG": "ORGANIZATION", "LOC": "LOCATION"}


def _bio_to_entities(text: str, tag_str: str) -> list:
    """Converts a stringified BIO tag list into [(entity_span, coarse_type), ...].
    Assumes tags align 1:1 with text.split() (verified against the source dataset)."""
    tags = ast.literal_eval(tag_str)
    tokens = text.split()

    entities = []
    current_tokens, current_type = [], None
    for token, tag in zip(tokens, tags):
        if tag.startswith("B-"):
            if current_tokens:
                entities.append((" ".join(current_tokens), current_type))
            current_tokens = [token]
            current_type = _COARSE_TYPE.get(tag[2:], "OTHER")
        elif tag.startswith("I-") and current_tokens:
            current_tokens.append(token)
        else:
            if current_tokens:
                entities.append((" ".join(current_tokens), current_type))
            current_tokens, current_type = [], None

    if current_tokens:
        entities.append((" ".join(current_tokens), current_type))

    return entities


def load_dataset(task_name: str, language: str = "english") -> list:
    """
    Loads a clean CSV for the given task and language.
    Returns a list of dicts with keys: id, text, label, text_2 (optional)

    task_name: sentiment, ner, summarisation, qa, paraphrase
    language: english or urdu
    """

    # Build the correct path
    if language == "urdu":
        folder = f"urdu_{task_name}"
    else:
        folder = task_name

    csv_path = f"datasets/processed/{folder}/clean.csv"

    # Check file exists
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Dataset not found: {csv_path}\n"
            f"Run scripts/01_download_datasets.py first."
        )

    # Load CSV
    df = pd.read_csv(csv_path, encoding="utf-8")
    logger.info(f"Loaded {len(df)} examples from {csv_path}")

    # Convert to list of dicts
    examples = []
    for _, row in df.iterrows():
        example = {
            "id": int(row["id"]),
            "text": str(row["text"]),
            "label": str(row["label"])
        }
        if task_name in ("ner", "urdu_ner"):
            example["label"] = _bio_to_entities(example["text"], str(row["label"]))
        # Include second sentence if it exists (paraphrase task)
        if "text_2" in df.columns and pd.notna(row.get("text_2")):
            example["text_2"] = str(row["text_2"])

        examples.append(example)

    logger.info(f"Dataset ready — task={task_name}, language={language}, examples={len(examples)}")
    return examples






