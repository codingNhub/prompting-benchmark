# Downloads all 5 datasets from HuggingFace, samples 100 examples each, saves clean CSVs.

import os
import random
import pandas as pd
from datasets import load_dataset

random.seed(42)

def download_dataset(task_name, hf_name, hf_config, split, label_map, text_column, label_column, n_samples=100):
    print(f"Downloading {task_name}...")

    # Skip if already downloaded
    output_path = f"datasets/processed/{task_name}/clean.csv"
    if os.path.exists(output_path):
        print(f"Already exists, skipping: {output_path}")
        return

    # Load dataset from Hugging Face
    if hf_config:
        dataset = load_dataset(hf_name, hf_config, verification_mode="no_checks")
    else:
        dataset = load_dataset(hf_name, verification_mode="no_checks")

    # Get the correct split
    data = dataset[split]

    # Filter English only for MultiNERD
    if task_name == "ner":
        data = data.filter(lambda x: x["lang"] == "en")

    # Sample 100 examples randomly
    indices = random.sample(range(len(data)), n_samples)
    sampled = data.select(indices)

# Build list of clean examples
    examples = []
    for item in sampled:
        raw_text = item[text_column]
        raw_label = item[label_column]

        # Handle list-type columns (NER tokens and tags)
        if isinstance(raw_text, list):
            text = " ".join(str(t) for t in raw_text)

            # Apply label_map to each tag in the list
            if label_map and isinstance(raw_label, list):
                label = [label_map.get(tag, "O") for tag in raw_label]
            else:
                label = raw_label

        # Handle scalar columns (all other tasks)
        else:
            text = raw_text.strip()

            if label_map:
                label = label_map[raw_label]
            elif isinstance(raw_label, dict):
                label = raw_label.get("value", str(raw_label)).strip()
            else:
                label = str(raw_label).strip()

        # Save second sentence for paraphrase task
        text_2 = item.get("sentence2", None)
        if text_2:
            text_2 = text_2.strip()

        if text:
            entry = {
                "id": len(examples),
                "text": text,
                "label": label
            }
            if text_2:
                entry["text_2"] = text_2
            examples.append(entry)
# Convert to DataFrame and save as CSV
    df = pd.DataFrame(examples)
    os.makedirs(f"datasets/processed/{task_name}", exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Saved {len(df)} examples to {output_path}")
    return df
# ── SENTIMENT: TweetEval ──────────────────────────────────────
download_dataset(
    task_name="sentiment",
    hf_name="cardiffnlp/tweet_eval",
    hf_config="sentiment",
    split="test",
    label_map={0: "Negative", 1: "Neutral", 2: "Positive"},
    text_column="text",
    label_column="label"
)

# ── NER: MultiNERD ────────────────────────────────────────────
download_dataset(
    task_name="ner",
    hf_name="Babelscape/multinerd",
    hf_config=None,
    split="test",
    label_map={
        0: "O",
        1: "B-PER", 2: "I-PER",
        3: "B-ORG", 4: "I-ORG",
        5: "B-LOC", 6: "I-LOC",
        7: "B-ANIM", 8: "I-ANIM",
        9: "B-BIO", 10: "I-BIO",
        11: "B-CEL", 12: "I-CEL",
        13: "B-DIS", 14: "I-DIS",
        15: "B-EVE", 16: "I-EVE",
        17: "B-FOOD", 18: "I-FOOD",
        19: "B-INST", 20: "I-INST",
        21: "B-MEDIA", 22: "I-MEDIA",
        23: "B-PLANT", 24: "I-PLANT",
        25: "B-MYTH", 26: "I-MYTH",
        27: "B-TIME", 28: "I-TIME",
        29: "B-VEHI", 30: "I-VEHI"
    },
    text_column="tokens",
    label_column="ner_tags"
)

# ── SUMMARISATION: XSum ───────────────────────────────────────
download_dataset(
    task_name="summarisation",
    hf_name="EdinburghNLP/xsum",
    hf_config=None,
    split="test",
    label_map={},
    text_column="document",
    label_column="summary"
)

# ── QA: TriviaQA ──────────────────────────────────────────────
download_dataset(
    task_name="qa",
    hf_name="trivia_qa",
    hf_config="rc.wikipedia",
    split="validation",
    label_map={},
    text_column="question",
    label_column="answer"
)

# ── PARAPHRASE: MRPC ──────────────────────────────────────────
download_dataset(
    task_name="paraphrase",
    hf_name="nyu-mll/glue",
    hf_config="mrpc",
    split="test",
    label_map={0: "Not Paraphrase", 1: "Paraphrase"},
    text_column="sentence1",
    label_column="label"
)
# ── URDU SENTIMENT: Roman Urdu ────────────────────────────────
download_dataset(
    task_name="urdu_sentiment",
    hf_name="community-datasets/roman_urdu",
    hf_config=None,
    split="train",
    label_map={0: "Negative", 1: "Neutral", 2: "Positive"},
    text_column="sentence",
    label_column="sentiment"
)

# ── URDU NER: mirfan899/urdu-ner ──────────────────────────────
download_dataset(
    task_name="urdu_ner",
    hf_name="mirfan899/urdu-ner",
    hf_config=None,
    split="train",
    label_map={
        0: "DATE",
        1: "PERSON",
        2: "ORGANIZATION",
        3: "O",
        4: "NUMBER",
        5: "LOCATION",
        6: "DESIGNATION",
        7: "TIME"
    },
    text_column="tokens",
    label_column="ner_tags"
)
print("All datasets downloaded successfully.")