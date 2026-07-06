# Baseline Scores for Comparison

## Dataset SOTA Reference Points

| Task | Dataset | Best Published Score | Type | Notes |
|------|---------|---------------------|------|-------|
| Sentiment | TweetEval | 73.7% macro-recall | Fine-tuned (TimeLM-21) | Prompting will score lower — expected |
| NER | WNUT-17 | ~60% F1 | Fine-tuned (CL-KL) | Very hard dataset. 40-50% from prompting is not failure |
| Summarisation | XSum | ~40 ROUGE-L | Fine-tuned (PEGASUS) | Prompting will score lower — expected |
| QA | TriviaQA | Varies by split | Fine-tuned + retrieval | Must specify closed-book split in paper |
| Paraphrase | MRPC | ~91% F1 | Fine-tuned (RoBERTa) | Cite GLUE leaderboard as reference |

## Key Papers Read

### Wang et al. 2022 — Self-Consistency (ICLR 2023)
- Self-consistency improves CoT by +17.9% on GSM8K
- Only tested on reasoning tasks — NOT on sentiment, NER, summarisation
- Limitation acknowledged by authors: higher computation cost
- Our paper addresses the gap: we test self-consistency across all task types

### Brown et al. 2020 — GPT-3 Few-Shot
- Few-shot prompting works but effectiveness varies significantly by task
- Zero-shot TriviaQA: 64.3%, Few-shot: 71.2%
- Supports our H1: technique effectiveness is task-dependent

## Important Notes for Paper Writing
- WNUT-17 is genuinely hard (SOTA ~60% F1) — low scores are expected, not failures
- TriviaQA: always specify "closed-book few-shot" split in methodology
- paperswithcode.com shut down July 2025 — use Hugging Face leaderboards instead