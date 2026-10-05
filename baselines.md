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

### Wang et al. 2023 — Self-Consistency (ICLR 2023)
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
These items match Section 6 (Limitations) of the paper word for word, so the two cannot disagree; the paper's text is defined in `scripts/build_paper.py`.

- Single model (openai/gpt-oss-20b via Groq), single random seed (42): no cross-model or run-to-run variance data. Paired bootstrap 95% intervals (`outputs/tables/bootstrap_ci.csv`) cover example-sampling uncertainty only; most within-task differences are not statistically distinguishable at n=100, and no multiple-comparison correction was applied.
- English-only scope: the Urdu extension was scoped and its data processed, but not evaluated in this release.
- Model and inference caveats. openai/gpt-oss-20b is a reasoning model: before its visible answer it produces hidden internal reasoning, and these hidden reasoning tokens count against the output-token limit. Every technique, including zero-shot, therefore involves some internal reasoning, which likely narrows the measurable benefit of explicit chain-of-thought prompting. It is also the main source of parse failures: 21 of the 30 failures in the reported results reached the output-token limit (1,500 tokens for sentiment, named entity recognition and paraphrase detection; 1,000 for question answering and summarisation), 20 of them with no visible answer at all. Of the other failures, six are structured-output summaries that did not close the required answer tag and three were caused by network errors rather than by the model. All failures are scored as incorrect.
- To limit truncation, question answering and summarisation were run with the provider's reasoning-effort setting set to low, while the other three tasks used the provider's default. This setting was introduced on 2026-07-28, after seven of the thirteen question-answering and summarisation results had been generated (zero-shot, few-shot, role and structured output on question answering; structured output, zero-shot and few-shot on summarisation), so comparisons within those two tasks span two inference configurations. One of these seven results was independently re-verified from raw model output; the other six were not individually re-checked.
- Corrections during data collection. Examples that failed to parse were individually re-queried, and this was not done evenly across techniques. The reported results include 46 re-queries of 44 examples: zero-shot 24 examples, few-shot CoT 9, CoT 6, reformulation 3, role prompting 1, structured output 1, and few-shot and self-consistency none. Of the 42 re-queried examples that had failed, 37 now have a valid answer and 5 remain failed. Flagged counts should therefore not be compared directly between techniques. Three re-queries were applied to examples that already had a valid answer: two returned the same answer, and one (example 48, CoT on sentiment) returned a different answer and has been restored to its original prediction. A further 34 logged re-queries (19 for self-consistency, 13 for zero-shot and 2 for few-shot CoT on question answering) belong to runs that were later discarded and regenerated in full, and do not affect any reported result. Finally, on 2026-07-28 the question-answering templates for CoT and few-shot CoT were edited to add a brevity instruction without a change to the template version number. Both of these results were regenerated in full on 2026-07-29, so every reported result uses the edited wording, but the version label alone does not distinguish the two wordings.
- Self-consistency was regenerated in full. An audit found that its three samples per example had been sent with the same random seed; in the original sentiment run the three samples gave the same answer on 97 of the 99 examples for which all three were logged. All three self-consistency results reported here were regenerated with seeds 42, 43 and 44 for the three samples, and API or network errors during the regeneration were retried rather than scored as failures. After regeneration the three samples agreed on 82 of 100 sentiment examples, 70 of 100 named entity recognition examples and 86 of 100 paraphrase examples. On paraphrase detection, agreement was about as high before the change (87 of 98 logged examples), so the high agreement reflects the model's own consistency at temperature 0.7 and not only the shared seed.
- Metric conventions. Sentiment and paraphrase scores are macro F1. TweetEval's official sentiment metric is macro-averaged recall, and GLUE reports binary F1 for MRPC, so these scores are not directly comparable to either public leaderboard. BERTScore uses a bert-base-uncased backbone and is rescaled against a baseline, which is why its values fall around 0.30 rather than the roughly 0.85 typical of unrescaled scores; absolute BERTScore values should be treated as indicative.
- Summarisation metrics do not detect factual errors. ROUGE-L and BERTScore measure overlap and similarity with a reference summary, so a fluent summary that states a wrong fact is not penalised. An informal manual check of a few summaries found names that the source article does not support. One article refers to the athlete Sanya Richards-Ross only by her surname; six of the seven techniques (all except few-shot CoT) called her "Emma", the first name of the journalist who interviewed her. Johnny Manziel, also named only by surname, was called "Robert", the first name of a lawyer quoted in the same article, by few-shot and structured output. Derek McInnes was called "Jim" by CoT and structured output, and the CoT summary of an article about David Cameron referred to "Prime Minister Boris Cameron". The check was not systematic, so how often such errors occur is not known.
- Class imbalance: sentiment Positive/Neutral/Negative = 18/48/34 and paraphrase Paraphrase/Not Paraphrase = 76/24; consider this when interpreting macro F1 and accuracy.
