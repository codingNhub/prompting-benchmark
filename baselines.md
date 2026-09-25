# Baseline Scores for Comparison

## Dataset SOTA Reference Points

| Task | Dataset | Best Published Score | Type | Notes |
|------|---------|---------------------|------|-------|
| Sentiment | TweetEval | 73.7% macro-recall | Fine-tuned (TimeLM-21) | Prompting will score lower — expected |
| NER | MultiNERD (English) | ~84% F1 | Fine-tuned (mBERT) | Large modern dataset. Check HF leaderboard for current SOTA |
| Summarisation | XSum | ~40 ROUGE-L | Fine-tuned (PEGASUS) | Prompting will score lower — expected |
| QA | TriviaQA | ~68% EM (closed-book) | Fine-tuned (T5) | Always specify closed-book split in paper |
| Paraphrase | MRPC | ~91% F1 | Fine-tuned (RoBERTa) | Cite GLUE leaderboard as reference |
| Urdu Sentiment | Roman Urdu (Sharf 2018) | ~78% F1 | Fine-tuned (BERT-Urdu) | **Scoped out of this release** — data pipeline exists, not evaluated |
| Urdu NER | mirfan899/urdu-ner | ~72% F1 | Fine-tuned | **Scoped out of this release** — data pipeline exists, not evaluated |

## Key Papers Read

### Liu et al. 2023 — Pre-train, Prompt, and Predict (ACM Computing Surveys)
- Primary gap evidence: Section 9 explicitly states systematic cross-task comparisons are limited
- Cross-lingual prompting identified as underexplored
- This is the foundational justification for our study

### Wang et al. 2022 — Self-Consistency (ICLR 2023)
- Self-consistency improves CoT by +17.9% on GSM8K
- Only tested on reasoning tasks — NOT on sentiment, NER, summarisation
- Limitation acknowledged by authors: higher computation cost
- Our study addresses the gap: we test self-consistency across all task types (except QA and summarisation, where majority voting over free-text output is undefined)

### Brown et al. 2020 — GPT-3 Few-Shot
- Few-shot prompting works but effectiveness varies significantly by task
- Zero-shot TriviaQA: 64.3%, Few-shot: 71.2%
- Supports our H1: technique effectiveness is task-dependent

### Wei et al. 2022 — Chain of Thought (NeurIPS 2022)
- CoT significantly improves reasoning and maths tasks
- Not tested on classification or NER tasks
- Our study tests CoT across all 5 completed task types

### Kojima et al. 2022 — Zero-Shot CoT
- "Let's think step by step" improves zero-shot reasoning
- Only evaluated on reasoning benchmarks
- Our study includes this as one of the 8 techniques

## Dataset Notes for Paper Writing
- Class imbalance: sentiment is Positive/Neutral/Negative = 18/48/34 and paraphrase is Paraphrase/Not Paraphrase = 76/24 — both imbalanced relative to a uniform split; note as a limitation when interpreting macro-F1 and accuracy.
- MultiNERD: filter English only (lang == "en") — stated in methodology
- TriviaQA: always specify "closed-book validation split" in methodology
- Paraphrase reported as macro-F1 (consistent with this project's standard across all classification tasks), not GLUE's official binary-F1 — not directly comparable to the published MRPC leaderboard without conversion
- paperswithcode.com shut down July 2025 — use Hugging Face leaderboards instead

## Scope Note
Urdu datasets (Roman Urdu sentiment, mirfan899/urdu-ner) were downloaded and processed during development, but prompt templates and experiments for these tasks were not completed in this release. Label scheme confirmed from mirfan899/Urdu GitHub repository for future reference: DATE(0), PERSON(1), ORGANIZATION(2), O(3), NUMBER(4), LOCATION(5), DESIGNATION(6), TIME(7). Urdu evaluation is documented as future work, not included in current results.

## Known Limitations
- Single model (openai/gpt-oss-20b via Groq), single random seed (42) — no cross-model or run-to-run variance data.
- No bootstrap confidence intervals — score differences between techniques are point estimates only.
- Seven QA/summarisation results were generated before a reasoning-efficiency setting was tuned on 2026-07-28. One of these seven was independently re-verified from raw model output and confirmed accurate. The remaining six were not individually re-checked, but no quality issues were observed in this group during review.
- BERTScore backbone is bert-base-uncased — treat absolute BERTScore values as indicative, not calibrated against stronger backbones.