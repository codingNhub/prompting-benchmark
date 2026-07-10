# Baseline Scores for Comparison

## Dataset SOTA Reference Points

| Task | Dataset | Best Published Score | Type | Notes |
|------|---------|---------------------|------|-------|
| Sentiment | TweetEval | 73.7% macro-recall | Fine-tuned (TimeLM-21) | Prompting will score lower — expected |
| NER | MultiNERD (English) | ~84% F1 | Fine-tuned (mBERT) | Large modern dataset. Check HF leaderboard for current SOTA |
| Summarisation | XSum | ~40 ROUGE-L | Fine-tuned (PEGASUS) | Prompting will score lower — expected |
| QA | TriviaQA | ~68% EM (closed-book) | Fine-tuned (T5) | Always specify closed-book split in paper |
| Paraphrase | MRPC | ~91% F1 | Fine-tuned (RoBERTa) | Cite GLUE leaderboard as reference |
| Urdu Sentiment | Roman Urdu (Sharf 2018) | ~78% F1 | Fine-tuned (BERT-Urdu) | Label noise known issue — acknowledged in limitations |
| Urdu NER | mirfan899/urdu-ner | ~72% F1 | Fine-tuned | Community dataset — treat SOTA as approximate |

## Key Papers Read

### Liu et al. 2023 — Pre-train, Prompt, and Predict (ACM Computing Surveys)
- Primary gap evidence: Section 9 explicitly states systematic cross-task comparisons are limited
- Cross-lingual prompting identified as underexplored
- This is the foundational justification for our entire study

### Wang et al. 2022 — Self-Consistency (ICLR 2023)
- Self-consistency improves CoT by +17.9% on GSM8K
- Only tested on reasoning tasks — NOT on sentiment, NER, summarisation
- Limitation acknowledged by authors: higher computation cost
- Our paper addresses the gap: we test self-consistency across all task types

### Brown et al. 2020 — GPT-3 Few-Shot
- Few-shot prompting works but effectiveness varies significantly by task
- Zero-shot TriviaQA: 64.3%, Few-shot: 71.2%
- Supports our H1: technique effectiveness is task-dependent

### Wei et al. 2022 — Chain of Thought (NeurIPS 2022)
- CoT significantly improves reasoning and maths tasks
- Not tested on classification or NER tasks
- Our paper tests CoT across all 5 task types

### Kojima et al. 2022 — Zero-Shot CoT
- "Let's think step by step" improves zero-shot reasoning
- Only evaluated on reasoning benchmarks
- Our paper includes this as one of the 8 techniques

## Dataset Notes for Paper Writing
- MultiNERD: filter English only (lang == "en") — stated in methodology
- TriviaQA: always specify "closed-book validation split" in methodology
- Roman Urdu sentiment: label noise acknowledged in limitations section
- mirfan899/urdu-ner: community dataset, annotation quality varies — acknowledge in limitations
- Urdu NER baseline is approximate — treat with caution in comparison
- paperswithcode.com shut down July 2025 — use Hugging Face leaderboards instead

Label scheme confirmed from mirfan899/Urdu GitHub repository.
Tags: DATE(0), PERSON(1), ORGANIZATION(2), O(3), NUMBER(4), LOCATION(5), DESIGNATION(6), TIME(7)