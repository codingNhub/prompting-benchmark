# Methodology: Prompting Technique Benchmark

## Research Question

Does the effectiveness of prompting techniques for large language models vary systematically by task type? This study evaluates 8 prompting techniques across 5 distinct NLP tasks to test whether technique effectiveness is task-dependent, addressing a gap identified in Liu et al. (2023), who note that systematic cross-task comparisons of prompting techniques remain limited in the literature.

## Model

openai/gpt-oss-20b, accessed via Groq's inference API. Temperature 0.0 for all techniques except self-consistency (0.7, per Wang et al. 2023). Random seed fixed at 42 across all experiments, except that self-consistency's three samples use seeds 42, 43 and 44 so they are drawn independently.

## Techniques Evaluated

1. **Zero-shot** — direct instruction, no examples
2. **Few-shot** — 3 in-context demonstrations, sampled per-instance with contamination prevention (the target example is always excluded from its own demonstration pool)
3. **Chain-of-Thought (CoT)** — "let's think step by step" reasoning prompt (Kojima et al. 2022)
4. **Role prompting** — model assigned a domain-expert persona
5. **Reformulation** — task instruction rephrased with explicit constraints
6. **Self-consistency** — 3 samples at temperature 0.7, each with its own seed (42, 43, 44), majority vote (Wang et al. 2023). Excluded for QA and summarisation, where majority voting over free-text generation is undefined.
7. **Structured output** — model required to produce output in a fixed schema
8. **Few-shot CoT** — combines demonstrations with step-by-step reasoning

## Tasks and Datasets

| Task | Dataset | Split | N |
|------|---------|-------|---|
| Sentiment classification | TweetEval | test | 100 |
| Named entity recognition | MultiNERD (English) | test | 100 |
| Abstractive summarisation | XSum | test | 100 |
| Question answering | TriviaQA (closed-book) | validation | 100 |
| Paraphrase detection | GLUE MRPC | test | 100 |

All datasets sampled to 100 examples with fixed seed 42 for reproducibility. Full dataset provenance and known class imbalances documented in `baselines.md`.

## Evaluation Metrics

- Sentiment: macro F1 (note: TweetEval's official sentiment metric is macro-averaged recall, so these scores are not directly comparable to the TweetEval leaderboard)
- NER: entity-level F1, exact span and type match (CoNLL convention)
- Summarisation: ROUGE-L and BERTScore (bert-base-uncased backbone)
- QA: exact match and token-level F1 (SQuAD convention, with article and punctuation normalisation)
- Uncertainty: paired percentile bootstrap, 1,000 resamples, 95% intervals (`src/bootstrap.py`, output in `outputs/tables/bootstrap_ci.csv`)
- Paraphrase: macro F1 (note: differs from GLUE's official binary-F1 convention; not directly comparable to the public leaderboard)

## Pipeline Integrity

All model outputs were extracted via a structured `<answer>` tag contract embedded in every prompt template, rather than free-text pattern matching, to ensure consistent and auditable parsing across all 8 techniques. Parse failures (missing tag, empty response, content-filter refusal) were counted as incorrect predictions in all metrics, not excluded — failure rates are reported alongside every score.

The pipeline underwent iterative internal audit across development. Measurement validity was verified iteratively during data collection; corrections made after some results existed are disclosed in Limitations (see `baselines.md`). Issues identified and corrected include: a metric-computation bug that created a phantom label class when scoring parse failures, insufficient generation token budgets causing truncated responses on complex inputs, a few-shot demonstration selection bug that could expose a test example to its own gold label, inconsistent brevity instructions across QA prompt templates, and self-consistency samples that all shared one random seed.

## Reproducibility

Every result is traceable to model name, prompt template version, normaliser version, and random seed, recorded per experiment in `outputs/results/results_master.csv`. Raw model predictions for every example are preserved in `outputs/predictions/` and every reported metric can be independently recomputed from these files.

## Limitations

The complete Limitations list, with all counts, is in `baselines.md` and is identical in substance to Section 6 of the paper. In brief: single model and single seed (bootstrap intervals cover example-sampling uncertainty only, with no multiple-comparison correction); a reasoning model whose hidden reasoning tokens count against the output limit; the reasoning-effort setting used for QA and summarisation only, introduced after 7 of those 13 results existed; re-queries of failed examples applied unevenly across techniques; example 48 (CoT, sentiment) restored after an erroneous re-query; self-consistency regenerated with seeds 42, 43 and 44 after its samples were found to share one seed; three failures caused by network errors; rescaled BERTScore; macro-F1 conventions that differ from the TweetEval and GLUE leaderboards; summarisation metrics that do not detect factual errors; and English-only scope.

## Results

See `results_summary.md` for the complete results table and discussion of findings across all 38 completed technique-task combinations.