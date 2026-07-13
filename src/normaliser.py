import re
from src.logger import get_logger

logger = get_logger("normaliser")

# Bump this whenever normalise()'s extraction logic changes, so results_master.csv
# can distinguish predictions parsed under different normaliser behavior.
NORMALISER_VERSION = "2.0"

ANSWER_TAG_RE = re.compile(r"<answer>(.*?)</answer>", re.DOTALL | re.IGNORECASE)


def normalise(raw_text: str, valid_labels: list = None) -> dict:
    """
    Universal normaliser for every technique and task. Extracts the content
    between <answer> and </answer> tags — the structured-output contract
    every prompt template now requires. Works identically whether or not
    reasoning text precedes the tag, so no technique-specific branching
    is needed. A missing tag is a parse failure, not a guess.

    valid_labels: for closed-label tasks (sentiment, paraphrase, NER types),
    the extracted content must exactly match one label (case-insensitive).
    Leave as None for free-text tasks (summarisation, qa) or for NER's
    raw entity-list content, where the extracted text is returned as-is.
    """
    if not raw_text or not raw_text.strip():
        return {"label": None, "status": "failed", "raw": raw_text}

    match = ANSWER_TAG_RE.search(raw_text)
    if not match:
        logger.warning(f"Parse failure — no <answer> tag in: {raw_text[:80]}")
        return {"label": None, "status": "failed", "raw": raw_text}

    content = match.group(1).strip()
    if not content:
        logger.warning(f"Parse failure — empty <answer> tag in: {raw_text[:80]}")
        return {"label": None, "status": "failed", "raw": raw_text}

    if valid_labels:
        content_lower = content.lower()
        exact = [label for label in valid_labels if label.lower() == content_lower]
        if len(exact) == 1:
            logger.info(f"Normalised: '{exact[0]}' from <answer> tag")
            return {"label": exact[0], "status": "ok", "raw": raw_text}
        logger.warning(f"Ambiguous <answer> content '{content}' — expected one of {valid_labels}")
        return {"label": None, "status": "ambiguous", "raw": raw_text}

    logger.info(f"Normalised free-text answer from <answer> tag: {content[:60]}")
    return {"label": content, "status": "ok", "raw": raw_text}


def parse_ner_entities(text: str) -> list:
    """
    Deserialises ENTITY | TYPE lines — already extracted from an <answer>
    tag by normalise() — into a list of (entity, type) tuples.
    Silently skips malformed lines.
    """
    if not text or not text.strip() or text.strip().upper() == "NONE":
        return []

    entities = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or line.upper() == "NONE":
            continue
        if "|" in line:
            parts = line.split("|")
            if len(parts) == 2:
                entity = parts[0].strip()
                entity_type = parts[1].strip().upper()
                if entity and entity_type:
                    entities.append((entity, entity_type))

    return entities
