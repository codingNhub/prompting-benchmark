# Loads prompt templates from YAML. Formats prompts with input text. Handles few-shot shuffling.
# Loads prompt templates from YAML and fills slots with dataset examples.

import os
import yaml
import random
from src.logger import get_logger

logger = get_logger("prompt_manager")


def load_template(technique: str, version: str = "1.0") -> dict:
    """
    Loads the YAML template file for a given technique.
    Returns the full template dict.
    """
    path = f"prompts/templates/{technique}/v{version}.yaml"

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Template not found: {path}\n"
            f"Check prompts/templates/{technique}/ folder."
        )

    with open(path, "r", encoding="utf-8") as f:
        template = yaml.safe_load(f)

    logger.info(f"Loaded template: {technique} v{version}")
    return template


def build_prompt(technique: str, task: str, example: dict,
                 few_shot_pool: list = None, version: str = "1.0") -> str:
    """
    Builds a complete prompt string from template + example data.

    technique: zero_shot, few_shot, cot, role, reformulation,
               self_consistency, structured_output, few_shot_cot
    task: sentiment, ner, summarisation, qa, paraphrase
    example: one dict from dataset_loader with keys id, text, label, text_2
    few_shot_pool: list of examples to draw few-shot demos from (not used in zero_shot)
    """

    template = load_template(technique, version)
    task_template = template["tasks"][task]["template"]

    # Fill in the main input
    prompt = task_template.replace("{input_text}", example["text"])

    # Fill in second sentence for paraphrase
    if "{input_text_2}" in prompt:
        text_2 = example.get("text_2", "")
        prompt = prompt.replace("{input_text_2}", text_2)

# Fill in few-shot examples
    if few_shot_pool and "{example_1_text}" in prompt:
        # For few_shot_cot — use YAML examples only, never the random pool
        # This keeps sentence/reasoning/label coherent
        if "examples" in template["tasks"][task]:
            yaml_examples = template["tasks"][task]["examples"]
            rng = random.Random(42)
            demos = rng.sample(yaml_examples, min(3, len(yaml_examples)))
            for i, demo in enumerate(demos, start=1):
                n = str(i)
                for key, value in demo.items():
                    prompt = prompt.replace(f"{{example_{n}_{key}}}", str(value))
        else:
            # For few_shot — use random pool
            rng = random.Random(42)
            demos = rng.sample(few_shot_pool, min(3, len(few_shot_pool)))
            for i, demo in enumerate(demos, start=1):
                n = str(i)
                prompt = prompt.replace(f"{{example_{n}_text}}", demo.get("text", ""))
                prompt = prompt.replace(f"{{example_{n}_label}}", demo.get("label", ""))
                prompt = prompt.replace(f"{{example_{n}_sentence1}}", demo.get("text", ""))
                prompt = prompt.replace(f"{{example_{n}_sentence2}}", demo.get("text_2", ""))

    # Fill YAML examples for techniques that use them (non-few-shot)
    elif "examples" in template["tasks"][task] and "{example_1_text}" in prompt:
        yaml_examples = template["tasks"][task]["examples"]
        rng = random.Random(42)
        demos = rng.sample(yaml_examples, min(3, len(yaml_examples)))
        for i, demo in enumerate(demos, start=1):
            n = str(i)
            for key, value in demo.items():
                prompt = prompt.replace(f"{{example_{n}_{key}}}", str(value))

    logger.info(f"Built prompt — technique={technique}, task={task}, id={example['id']}")
    return prompt




