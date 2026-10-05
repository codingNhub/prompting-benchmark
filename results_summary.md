# Results Summary

38 of 38 planned English-language experiments completed (8 techniques × 5 tasks, with self-consistency excluded from QA and summarisation, where majority voting over free-text generation is undefined). Each experiment uses 100 examples. Full per-example predictions and raw model outputs are in `outputs/predictions/`; full metrics in `outputs/results/results_master.csv`; bootstrap intervals in `outputs/tables/bootstrap_ci.csv`. The tables in the paper are generated from these same files by `scripts/build_paper.py`.

Techniques are ranked by the primary metric; tied techniques are listed alphabetically. "Flagged" is the number of examples (out of 100) with a parse failure, scored as incorrect. 95% CIs are paired percentile bootstrap intervals (`python -m src.bootstrap`, 1,000 resamples).

## Sentiment Classification (macro F1)

| Technique | Macro F1 | 95% CI | Flagged |
|---|---|---|---|
| Few-shot CoT | 0.7159 | 0.618–0.800 | 0 |
| Few-shot | 0.6924 | 0.595–0.780 | 0 |
| Role | 0.6673 | 0.573–0.750 | 0 |
| Zero-shot | 0.6663 | 0.568–0.758 | 0 |
| Structured output | 0.6583 | 0.567–0.745 | 0 |
| CoT | 0.6577 | 0.563–0.746 | 0 |
| Self-consistency | 0.6309 | 0.535–0.721 | 0 |
| Reformulation | 0.6047 | 0.504–0.699 | 0 |

**Finding:** Few-shot CoT scored highest (0.7159), but its lead over few-shot (0.6924) is within sampling noise; the bootstrap distinguishes it only from self-consistency and reformulation. CoT alone (0.6577) scored slightly below zero-shot (0.6663). Self-consistency, despite three model calls per example, scored below zero-shot (0.6309), and reformulation scored lowest (0.6047).

## Named Entity Recognition (entity-level F1)

| Technique | Entity F1 | 95% CI | Flagged |
|---|---|---|---|
| Reformulation | 0.7692 | 0.694–0.834 | 4 |
| Few-shot | 0.7573 | 0.689–0.814 | 0 |
| CoT | 0.7524 | 0.691–0.808 | 1 |
| Structured output | 0.7516 | 0.680–0.815 | 2 |
| Self-consistency | 0.7500 | 0.682–0.808 | 0 |
| Zero-shot | 0.7500 | 0.680–0.814 | 2 |
| Role | 0.7483 | 0.678–0.813 | 3 |
| Few-shot CoT | 0.6957 | 0.612–0.776 | 0 |

**Finding:** Seven of the eight techniques scored between 0.748 and 0.769. Reformulation scored highest despite four flagged examples, but its lead over few-shot is within sampling noise. Self-consistency and zero-shot tied at exactly 0.7500. Few-shot CoT scored lowest (0.6957) and is the only technique the bootstrap distinguishes from reformulation.

## Abstractive Summarisation (ROUGE-L / BERTScore)

| Technique | ROUGE-L | 95% CI | BERTScore F1 | Flagged |
|---|---|---|---|---|
| Few-shot CoT | 0.1801 | 0.168–0.193 | 0.3044 | 0 |
| Structured output | 0.1800 | 0.162–0.196 | 0.2997 | 6 |
| Zero-shot | 0.1774 | 0.163–0.192 | 0.3105 | 0 |
| Few-shot | 0.1761 | 0.163–0.190 | 0.3020 | 0 |
| Role | 0.1739 | 0.158–0.188 | 0.3032 | 0 |
| CoT | 0.1715 | 0.159–0.184 | 0.3056 | 0 |
| Reformulation | 0.1709 | 0.155–0.186 | 0.2977 | 0 |

**Finding:** All techniques scored well below the fine-tuned PEGASUS baseline (~0.40 ROUGE-L). All seven fell within 0.010 ROUGE-L of each other (0.1709 to 0.1801). Few-shot CoT ranked first on ROUGE-L, 0.0001 ahead of structured output; zero-shot had the highest BERTScore; reformulation was lowest on both metrics. Neither metric detects factual errors in the summaries (see Known Limitations).

## Question Answering (exact match / token F1)

| Technique | Exact Match | 95% CI | Token F1 | Flagged |
|---|---|---|---|---|
| Reformulation | 0.59 | 0.50–0.68 | 0.6453 | 0 |
| Few-shot | 0.55 | 0.46–0.64 | 0.6296 | 0 |
| Role | 0.55 | 0.46–0.64 | 0.6131 | 0 |
| Structured output | 0.55 | 0.46–0.64 | 0.5999 | 2 |
| CoT | 0.53 | 0.43–0.63 | 0.5894 | 1 |
| Few-shot CoT | 0.52 | 0.43–0.62 | 0.5963 | 1 |
| Zero-shot | 0.51 | 0.42–0.61 | 0.5777 | 2 |

**Finding:** Reformulation scored highest on exact match (0.59) and token F1, four percentage points ahead of few-shot, role and structured output (0.55 each); the lead is within sampling noise, and the bootstrap distinguishes reformulation only from zero-shot (0.51), which scored lowest. CoT (0.53) and few-shot CoT (0.52) scored below few-shot, role and structured output, and above zero-shot.

## Paraphrase Detection (macro F1)

| Technique | Macro F1 | 95% CI | Flagged |
|---|---|---|---|
| Reformulation | 0.7472 | 0.647–0.840 | 0 |
| Role | 0.7335 | 0.631–0.826 | 1 |
| Self-consistency | 0.7270 | 0.635–0.816 | 0 |
| Zero-shot | 0.7040 | 0.603–0.790 | 1 |
| Few-shot | 0.6970 | 0.596–0.785 | 2 |
| Few-shot CoT | 0.6923 | 0.597–0.787 | 0 |
| Structured output | 0.6495 | 0.549–0.740 | 1 |
| CoT | 0.6464 | 0.543–0.741 | 1 |

**Finding:** Reformulation scored highest (0.7472), followed by role (0.7335) and self-consistency (0.7270), but its lead over role is within sampling noise. Structured output (0.6495) and CoT (0.6464) scored lowest and are the only two techniques the bootstrap distinguishes from reformulation. Reformulation's result did not carry over to sentiment classification, the other classification task, where it scored lowest.

## Cross-Task Synthesis

**No technique reliably dominated across the five tasks, and most differences are within sampling noise.** The top-scoring technique changed with the task: reformulation on NER, QA and paraphrase detection, and few-shot CoT on sentiment and summarisation (ROUGE-L). Each of these two techniques also scored lowest somewhere: reformulation on sentiment and on both summarisation metrics, and few-shot CoT on NER. Zero-shot CoT never scored highest and ranked last on paraphrase detection. Self-consistency (three model calls per example) never scored highest: seventh of eight on sentiment, tied with zero-shot mid-table on NER, third of eight on paraphrase. Few-shot ranked second on sentiment, NER and QA (tied on QA), and zero-shot had the highest summarisation BERTScore.

These rankings carry substantial uncertainty. The paired bootstrap compared each task's top-scoring technique with each of the others, 33 comparisons in all. Only 7 were distinguishable at the 95% level: few-shot CoT over self-consistency and over reformulation on sentiment; reformulation over few-shot CoT on NER; few-shot CoT over CoT on summarisation (lower bound 0.0001); reformulation over zero-shot on QA; and reformulation over structured output and over CoT on paraphrase. On no task was the top-scoring technique distinguishable from the runner-up; in particular, reformulation's lead was not distinguishable on any of the three tasks it led. No multiple-comparison correction was applied, so even these seven differences should be read cautiously.

Self-consistency's weak showing has two possible explanations that this study cannot separate: majority voting adds little when the three samples mostly agree (82/100 sentiment, 70/100 NER, 86/100 paraphrase), and its samples are drawn at temperature 0.7 while every other technique runs at 0.0, so each sample is noisier than a single greedy answer.

Practical advice is therefore cautious and task-specific: test a small set of inexpensive candidates (zero-shot, few-shot, a reformulated instruction) on the task at hand rather than adopting any technique by default.

## Known Limitations

The full Limitations list, with all counts, is in `baselines.md` and matches Section 6 of the paper. In brief: single model and single seed; bootstrap intervals cover example-sampling uncertainty only, with no multiple-comparison correction; uneven re-queries across techniques (flagged counts are not directly comparable); a reasoning-effort setting used for QA and summarisation only and introduced after 7 of those 13 results existed; summarisation metrics that do not detect factual errors; and English-only scope.
