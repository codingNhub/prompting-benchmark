# Applies 5 normalisation rules to extract clean labels from raw model responses.
# Extracts clean labels from raw model responses using 5 normalisation rules.

import re
from src.logger import get_logger

logger = get_logger("normaliser")


def normalise(raw_text: str, valid_labels: list) -> dict:
    """
    Applies 5 normalisation rules to extract a clean label from raw model output.

    Returns a dict with:
        - label: the clean extracted label or None
        - status: 'ok', 'ambiguous', or 'failed'
        - raw: the original raw text for logging
    """

    # Rule 1 — lowercase everything
    text = raw_text.lower().strip()

    # Rule 2 — lowercase the valid labels for comparison
    labels_lower = [l.lower() for l in valid_labels]

    # Rule 3 — search for each valid label anywhere in the response
    found = []
    for i, label in enumerate(labels_lower):
        # Use word boundary to avoid partial matches
        pattern = r'\b' + re.escape(label) + r'\b'
        if re.search(pattern, text):
            found.append(valid_labels[i])  # keep original casing

    # Rule 4 — if two or more labels found, flag as ambiguous
    if len(found) > 1:
        logger.warning(f"Ambiguous response — found {found} in: {raw_text[:80]}")
        return {
            "label": None,
            "status": "ambiguous",
            "raw": raw_text
        }

    # Rule 5 — if no label found, flag as parse failure
    if len(found) == 0:
        logger.warning(f"Parse failure — no label found in: {raw_text[:80]}")
        return {
            "label": None,
            "status": "failed",
            "raw": raw_text
        }

    # Clean success — return the single found label
    logger.info(f"Normalised: '{found[0]}' from response: {raw_text[:60]}")
    return {
        "label": found[0],
        "status": "ok",
        "raw": raw_text
    }


def normalise_ner(raw_text: str) -> list:
    """
    Parses NER model output in ENTITY | TYPE format.
    Returns a list of (entity, type) tuples.
    """
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


    # Quick test — delete before submission
    labels = ["Positive", "Negative", "Neutral"]

    # Test 1 — clean response
    r1 = normalise("The sentiment is Positive.", labels)
    print(f"Test 1: {r1}")

    # Test 2 — messy response
    r2 = normalise("Based on my analysis this is clearly a positive sentence.", labels)
    print(f"Test 2: {r2}")

    # Test 3 — ambiguous
    r3 = normalise("This could be Positive or Negative.", labels)
    print(f"Test 3: {r3}")

    # Test 4 — failed
    r4 = normalise("I am not sure about this one.", labels)
    print(f"Test 4: {r4}")

    # Test 5 — NER
    r5 = normalise_ner("Imran Khan | PERSON\nLahore | LOCATION")
    print(f"Test 5: {r5}")