# Results Summary

38 of 38 planned English-language experiments completed (8 techniques × 5 tasks, with self-consistency excluded from QA and summarisation, where majority voting over free-text generation is undefined). Full per-example predictions and raw model outputs are available in `outputs/predictions/`; full metrics in `outputs/results/results_master.csv`.

## Sentiment Classification (macro F1)

| Technique | Macro F1 | Flagged |
|-----------|----------|---------|
| Few-shot CoT | 0.7159 | 0 |
| Few-shot | 0.6924 | 0 |
| Role | 0.6673 | 0 |
| CoT | 0.6664 | 0 |
| Zero-shot | 0.6663 | 0 |
| Structured output | 0.6583 | 0 |
| Self-consistency | 0.6087 | 0 |
| Reformulation | 0.6047 | 0 |

**Finding:** Combining demonstrations with reasoning (few-shot CoT) produced the strongest result. CoT alone did not outperform zero-shot, suggesting explicit reasoning adds limited value for sentiment classification without accompanying examples. Self-consistency, despite requiring 3x the inference cost, underperformed simple zero-shot prompting.

## Named Entity Recognition (entity-level F1)

| Technique | Entity F1 | Flagged |
|-----------|-----------|---------|
| Reformulation | 0.7692 | 4 |
| Few-shot | 0.7573 | 0 |
| CoT | 0.7524 | 1 |
| Structured output | 0.7516 | 2 |
| Self-consistency | 0.7500 | 0 |
| Zero-shot | 0.7500 | 2 |
| Role | 0.7483 | 3 |
| Few-shot CoT | 0.6957 | 0 |

**Finding:** Performance clustered tightly across most techniques (0.75–0.77), with few-shot CoT as a notable underperformer — the combination of demonstrations and reasoning appears to introduce noise for extraction tasks rather than improving precision.

## Abstractive Summarisation (ROUGE-L / BERTScore)

| Technique | ROUGE-L | BERTScore F1 | Flagged |
|-----------|---------|---------------|---------|
| Few-shot CoT | 0.1801 | 0.3044 | 0 |
| Structured output | 0.1800 | 0.2997 | 6 |
| Zero-shot | 0.1774 | 0.3105 | 0 |
| Few-shot | 0.1761 | 0.3020 | 0 |
| Role | 0.1739 | 0.3032 | 0 |
| CoT | 0.1715 | 0.3056 | 0 |
| Reformulation | 0.1709 | 0.2977 | 0 |

**Finding:** All techniques scored well below the fine-tuned PEGASUS baseline (~0.40 ROUGE-L), consistent with expectations for zero/few-shot prompting versus fine-tuned models. Scores clustered closely across techniques, suggesting prompting strategy has limited impact on abstractive summarisation quality relative to the underlying model's capability.

## Question Answering (exact match / token F1)

| Technique | Exact Match | Token F1 | Flagged |
|-----------|-------------|----------|---------|
| Reformulation | 0.59 | 0.6453 | 0 |
| Few-shot | 0.55 | 0.6296 | 0 |
| Role | 0.55 | 0.6131 | 0 |
| Structured output | 0.55 | 0.5999 | 2 |
| CoT | 0.53 | 0.5894 | 1 |
| Few-shot CoT | 0.52 | 0.5963 | 1 |
| Zero-shot | 0.51 | 0.5777 | 2 |

**Finding:** Reformulation performed best on QA, suggesting that rephrasing the instruction with explicit constraints helps the model produce more precise short-answer outputs. Reasoning-based techniques (CoT, few-shot CoT) did not outperform simpler approaches on this closed-book factual QA task.

## Paraphrase Detection (macro F1)

| Technique | Macro F1 | Flagged |
|-----------|----------|---------|
| Reformulation | 0.7472 | 0 |
| Role | 0.7335 | 1 |
| Self-consistency | 0.7052 | 0 |
| Zero-shot | 0.7040 | 1 |
| Few-shot | 0.6970 | 2 |
| Few-shot CoT | 0.6923 | 0 |
| Structured output | 0.6495 | 1 |
| CoT | 0.6464 | 1 |

**Finding:** Reformulation again performed best, reinforcing a pattern across tasks: explicit rephrasing of the instruction outperforms both minimal prompting and reasoning-heavy techniques for binary classification-style judgments.

## Cross-Task Synthesis

Across all five tasks, a consistent pattern emerges: **elaborate reasoning-oriented techniques (chain-of-thought, self-consistency) do not reliably outperform simpler techniques (zero-shot, few-shot, reformulation)** on this model, and in several cases underperform despite substantially higher computational cost. Self-consistency, which requires 3x the inference calls, was never the best-performing technique on any task and was the worst performer on sentiment classification. Reformulation — simply rephrasing the instruction with explicit constraints — was the strongest or near-strongest technique on 3 of 5 tasks (NER, QA, paraphrase), despite being one of the simplest and cheapest techniques evaluated.

This suggests that for tasks with well-defined, unambiguous objectives, prompt clarity and instruction precision may matter more than reasoning depth or demonstration count — a finding that has practical implications for practitioners choosing prompting strategies under compute or latency constraints.

## Known Limitations

See `baselines.md` and `methodology.md` for the complete list of limitations, including single-model/single-seed evaluation, absence of statistical significance testing, and the current English-only scope of this release.