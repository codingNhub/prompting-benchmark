# Prompting Technique Benchmark

A systematic empirical comparison of 8 prompting techniques across 5 NLP tasks, evaluated on a single open-weight LLM (openai/gpt-oss-20b via Groq).

## Techniques evaluated
Zero-shot, Few-shot, Chain-of-Thought (CoT), Role prompting, Reformulation, Self-consistency, Structured output, Few-shot CoT

## Tasks evaluated
Sentiment classification (TweetEval), Named Entity Recognition (MultiNERD), Abstractive summarisation (XSum), Question answering (TriviaQA), Paraphrase detection (GLUE MRPC)

## Status
All 5 tasks × 8 techniques complete (38/38 combinations, self-consistency excluded from QA and summarisation where majority voting is undefined for free-text generation). Results in `outputs/results/results_master.csv`, raw predictions in `outputs/predictions/`.

## Key findings
See `methodology.md` and `baselines.md` for full methodology, per-task results, and comparison against published baselines.

## Reproducibility
Model: openai/gpt-oss-20b (Groq, temperature=0.0 except self-consistency at 0.7). Random seed: 42, fixed across all experiments. Dataset sources, versions, and known limitations documented in `baselines.md`.

## Scope
This benchmark covers English-language tasks only. Cross-lingual extension (Urdu) was scoped during development but is not included in this release.