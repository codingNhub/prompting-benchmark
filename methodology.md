# Methodology: Prompting Technique Benchmark

## Research Question

Does the effectiveness of prompting techniques for large language models vary systematically by task type? This study evaluates 8 prompting techniques across 5 distinct NLP tasks to test whether technique effectiveness is task-dependent, addressing a gap identified in Liu et al. (2023), who note that systematic cross-task comparisons of prompting techniques remain limited in the literature.

## Model

openai/gpt-oss-20b, accessed via Groq's inference API. Temperature 0.0 for all techniques except self-consistency (0.7, per Wang et al. 2022). Random seed fixed at 42 across all experiments.

## Techniques Evaluated

1. **Zero-shot** — direct instruction, no examples
2. **Few-shot** — 3 in-context demonstrations, sampled per-instance with contamination prevention (the target example is always excluded from its own demonstration pool)
3. **Chain-of-Thought (CoT)** — "let's think step by step" reasoning prompt (Kojima et al. 2022)
4. **Role prompting** — model assigned a domain-expert persona
5. **Reformulation** — task instruction rephrased with explicit constraints
6. **Self-consistency** — 3 samples at temperature 0.7, majority vote (Wang et al. 2022). Excluded for QA and summarisation, where majority voting over free-text generation is undefined.
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

- Sentiment: macro F1 (TweetEval convention)
- NER: entity-level F1, exact span and type match (CoNLL convention)
- Summarisation: ROUGE-L and BERTScore (bert-base-uncased backbone)
- QA: exact match and token-level F1 (SQuAD convention, with article and punctuation normalisation)
- Paraphrase: macro F1 (note: differs from GLUE's official binary-F1 convention; not directly comparable to the public leaderboard)

## Pipeline Integrity

All model outputs were extracted via a structured `<answer>` tag contract embedded in every prompt template, rather than free-text pattern matching, to ensure consistent and auditable parsing across all 8 techniques. Parse failures (missing tag, empty response, content-filter refusal) were counted as incorrect predictions in all metrics, not excluded — failure rates are reported alongside every score.

The pipeline underwent iterative internal audit across development, identifying and correcting several measurement issues before final results were generated, including: a metric-computation bug that created a phantom label class when scoring parse failures, insufficient generation token budgets causing truncated responses on complex inputs, a few-shot demonstration selection bug that could expose a test example to its own gold label, and inconsistent brevity instructions across QA prompt templates. All fixes and their verification are documented in the project's audit history.

## Reproducibility

Every result is traceable to model name, prompt template version, normaliser version, and random seed, recorded per experiment in `outputs/results/results_master.csv`. Raw model predictions for every example are preserved in `outputs/predictions/` and every reported metric can be independently recomputed from these files.

## Limitations

See `baselines.md` for the complete list, including: single-model/single-seed evaluation (no confidence intervals), scope limited to English-language tasks in this release, and dataset-specific caveats (class imbalance in sentiment and paraphrase, BERTScore backbone choice).

## Results

See `results_summary.md` for the complete results table and discussion of findings across all 38 completed technique-task combinations.