# Prompting Technique Benchmark

A systematic empirical comparison of 8 prompting techniques across 5 NLP tasks, evaluated on a single open-weight LLM (openai/gpt-oss-20b via Groq).

## Techniques evaluated
Zero-shot, Few-shot, Chain-of-Thought (CoT), Role prompting, Reformulation, Self-consistency, Structured output, Few-shot CoT

## Tasks evaluated
Sentiment classification (TweetEval), Named Entity Recognition (MultiNERD), Abstractive summarisation (XSum), Question answering (TriviaQA), Paraphrase detection (GLUE MRPC)

## Status
Complete: 38 of the 40 nominal technique–task combinations (5 tasks × 8 techniques). Self-consistency is excluded from QA and summarisation, where majority voting over free-text generation is undefined, so all 38 applicable combinations were run. Results in `outputs/results/results_master.csv`, raw predictions in `outputs/predictions/`.

## Key findings
See `results_summary.md` for per-task results, bootstrap confidence intervals, and the cross-task synthesis. Methodology is in `methodology.md`; published baselines, dataset notes, and the full list of limitations are in `baselines.md`.

## Reproducibility
Model: openai/gpt-oss-20b (Groq, temperature=0.0 except self-consistency at 0.7). Random seed: 42, fixed across all experiments (self-consistency's three samples use seeds 42, 43 and 44). Dataset sources, versions, and known limitations documented in `baselines.md`.

## Scope
This benchmark covers English-language tasks only. Cross-lingual extension (Urdu) was scoped during development but is not included in this release.