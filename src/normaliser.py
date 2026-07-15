import re
from src.logger import get_logger

logger = get_logger("normaliser")

# Bump this whenever normalise()'s extraction logic changes, so results_master.csv
# can distinguish predictions parsed under different normaliser behavior.
NORMALISER_VERSION = "2.0"

ANSWER_TAG_RE = re.compile(r"<answer>(.*?)</answer>", re.DOTALL | re.IGNORECASE)


def normalise(raw_text: str, valid_labels: list = None) -> dict:
    if not raw_text or not raw_text.strip():
        return {"label": None, "status": "failed", 
                "reason": "empty_response", "raw": raw_text}

    # Check for content refusal
    refusal_phrases = ["i cannot", "i'm sorry", "i am sorry", 
                       "i can't help", "i'm not able", "i cannot help",
                       "not appropriate", "inappropriate"]
    raw_lower = raw_text.lower()
    if any(phrase in raw_lower for phrase in refusal_phrases):
        if not ANSWER_TAG_RE.search(raw_text):
            return {"label": None, "status": "failed",
                    "reason": "content_refusal", "raw": raw_text}

    match = ANSWER_TAG_RE.search(raw_text)
    if not match:
        return {"label": None, "status": "failed",
                "reason": "no_tag", "raw": raw_text}
    if ANSWER_TAG_RE.search(raw_text, match.end()):
        return {"label": None, "status": "ambiguous",
                "reason": "multiple_tags", "raw": raw_text}

    content = match.group(1).strip()
    if not content:
        return {"label": None, "status": "failed",
                "reason": "empty_tag", "raw": raw_text}

    if valid_labels:
        content_lower = content.lower()
        exact = [label for label in valid_labels if label.lower() == content_lower]
        if len(exact) == 1:
            logger.info(f"Normalised: '{exact[0]}' from <answer> tag")
            return {"label": exact[0], "status": "ok", 
                    "reason": "", "raw": raw_text}
        return {"label": None, "status": "ambiguous",
                "reason": "ambiguous_content", "raw": raw_text}

    logger.info(f"Normalised free-text answer from <answer> tag: {content[:60]}")
    return {"label": content, "status": "ok", "reason": "", "raw": raw_text}

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
