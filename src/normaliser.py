import re
from src.logger import get_logger

logger = get_logger("normaliser")


def normalise(raw_text: str, valid_labels: list) -> dict:
    """
    Applies 5 normalisation rules to extract clean labels from raw model responses.
    Returns a dict with label, status (ok/ambiguous/failed), and raw response.
    """
    if not raw_text or not raw_text.strip():
        return {"label": None, "status": "failed", "raw": raw_text}

    text = raw_text.lower().strip()

    # Sort labels by length descending — check longer labels first
    # This prevents "Paraphrase" matching inside "Not Paraphrase"
    sorted_labels = sorted(valid_labels, key=len, reverse=True)

    found = []
    matched_positions = []

    for label in sorted_labels:
        pattern = r'\b' + re.escape(label.lower()) + r'\b'
        match = re.search(pattern, text)
        if match:
            start, end = match.start(), match.end()
            overlap = any(s < end and start < e for s, e in matched_positions)
            if not overlap:
                found.append(label)
                matched_positions.append((start, end))

    if len(found) > 1:
        logger.warning(f"Ambiguous response — found {found} in: {raw_text[:80]}")
        return {"label": None, "status": "ambiguous", "raw": raw_text}

    if len(found) == 0:
        logger.warning(f"Parse failure — no label found in: {raw_text[:80]}")
        return {"label": None, "status": "failed", "raw": raw_text}

    logger.info(f"Normalised: '{found[0]}' from response: {raw_text[:60]}")
    return {"label": found[0], "status": "ok", "raw": raw_text}


def normalise_cot(raw_text: str, valid_labels: list) -> dict:
    """
    Extracts label from CoT responses by looking at the final lines only.
    CoT reasoning contains all label words so full-text search fails.
    Searches from bottom up and returns first line with exactly one label.
    """
    if not raw_text or not raw_text.strip():
        return {"label": None, "status": "failed", "raw": raw_text}

    lines = [l.strip() for l in raw_text.strip().split("\n") if l.strip()]

    for line in reversed(lines):
        line_lower = line.lower()
        sorted_labels = sorted(valid_labels, key=len, reverse=True)
        found = []
        matched_positions = []

        for label in sorted_labels:
            pattern = r'\b' + re.escape(label.lower()) + r'\b'
            match = re.search(pattern, line_lower)
            if match:
                start, end = match.start(), match.end()
                overlap = any(s < end and start < e for s, e in matched_positions)
                if not overlap:
                    found.append(label)
                    matched_positions.append((start, end))

        if len(found) == 1:
            logger.info(f"CoT normalised: '{found[0]}' from last lines")
            return {"label": found[0], "status": "ok", "raw": raw_text}

    # If nothing found in last lines, fall back to full text search
    return normalise(raw_text, valid_labels)


def normalise_ner(raw_text: str) -> list:
    """
    Parses NER model output in ENTITY | TYPE format.
    Returns a list of (entity, type) tuples.
    Silently skips malformed lines.
    """
    if not raw_text or not raw_text.strip():
        return []

    entities = []
    lines = raw_text.strip().split("\n")

    for line in lines:
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