# One-off script to assemble the scholarship-application paper as a .docx
# from methodology.md, results_summary.md, and baselines.md. Not part of the
# experiment pipeline — run manually, not imported elsewhere.
# Result tables are read from outputs/results/results_master.csv and
# outputs/tables/bootstrap_ci.csv; the prose is written by hand and must be
# checked against those files whenever they change.

import csv
from decimal import Decimal, ROUND_HALF_UP

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def add_page_number_field(paragraph):
    run = paragraph.add_run()
    fld_begin = OxmlElement('w:fldChar')
    fld_begin.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = 'PAGE'
    fld_end = OxmlElement('w:fldChar')
    fld_end.set(qn('w:fldCharType'), 'end')
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)


def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Light Grid Accent 1'
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        for p in hdr_cells[i].paragraphs:
            for r in p.runs:
                r.bold = True
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
    doc.add_paragraph()
    return table


RESULTS_PATH = "outputs/results/results_master.csv"
CI_PATH = "outputs/tables/bootstrap_ci.csv"

TECHNIQUE_NAMES = {
    "zero_shot": "Zero-shot", "few_shot": "Few-shot", "cot": "CoT", "role": "Role",
    "reformulation": "Reformulation", "self_consistency": "Self-consistency",
    "structured_output": "Structured output", "few_shot_cot": "Few-shot CoT",
}

# task: (primary metric, its decimals, [(secondary column header, metric)], CI decimals)
TABLE_SPECS = {
    "sentiment": ("macro_f1", 4, [], 3),
    "ner": ("entity_f1", 4, [], 3),
    "summarisation": ("rouge_l", 4, [("BERTScore F1", "bert_f1")], 3),
    "qa": ("exact_match", 2, [("Token F1", "token_f1")], 2),
    "paraphrase": ("macro_f1", 4, [], 3),
}
PRIMARY_HEADERS = {"macro_f1": "Macro F1", "entity_f1": "Entity F1",
                   "rouge_l": "ROUGE-L", "exact_match": "Exact Match"}


def fmt(value, decimals):
    """Rounds half up from the CSV's decimal text, as a reader rounding by hand would."""
    return str(Decimal(value).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP))


def load_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def result_table_rows(task):
    """Headers and rows for one task, ranked by the primary metric (ties by technique key)."""
    metric, decimals, secondary, ci_decimals = TABLE_SPECS[task]
    results = [r for r in load_csv(RESULTS_PATH)
               if r["task"] == task and r["language"] == "english"]
    ci = {r["technique"]: r for r in load_csv(CI_PATH) if r["task"] == task}
    results.sort(key=lambda r: (-float(r[metric]), r["technique"]))
    headers = ["Technique", PRIMARY_HEADERS[metric], "95% CI"] + [h for h, _ in secondary] + ["Flagged"]
    rows = []
    for r in results:
        b = ci[r["technique"]]
        assert b["metric"] == metric and abs(float(b["point"]) - float(r[metric])) < 1e-4, \
            f"bootstrap_ci.csv is out of date for {task}/{r['technique']}"
        rows.append([TECHNIQUE_NAMES[r["technique"]],
                     fmt(r[metric], decimals),
                     f"{fmt(b['ci_low'], ci_decimals)}–{fmt(b['ci_high'], ci_decimals)}"]
                    + [fmt(r[m], 4) for _, m in secondary]
                    + [str(int(r["flagged_count"]))])
    return headers, rows


# Limitations paragraphs, shared word for word with the Known Limitations list in
# baselines.md. Every number here was counted from the final prediction files,
# outputs/rerun_log.csv and logs/experiment.log.
LIMITATIONS = {
    "model": (
        "Model and inference caveats. openai/gpt-oss-20b is a reasoning model: before its "
        "visible answer it produces hidden internal reasoning, and these hidden reasoning "
        "tokens count against the output-token limit. Every technique, including zero-shot, "
        "therefore involves some internal reasoning, which likely narrows the measurable "
        "benefit of explicit chain-of-thought prompting. It is also the main source of parse "
        "failures: 21 of the 30 failures in the reported results reached the "
        "output-token limit (1,500 tokens for sentiment, named entity recognition and "
        "paraphrase detection; 1,000 for question answering and summarisation), 20 of "
        "them with no visible answer at all. Of the other failures, six are "
        "structured-output summaries that did not close the required answer tag and three "
        "were caused by network errors rather than by the model. All failures are scored as "
        "incorrect."
    ),
    "inference": (
        "To limit truncation, question answering and summarisation were run with the "
        "provider's reasoning-effort setting set to low, while the other three tasks used the "
        "provider's default. This setting was introduced on 2026-07-28, after seven of the "
        "thirteen question-answering and summarisation results had been generated (zero-shot, "
        "few-shot, role and structured output on question answering; structured output, "
        "zero-shot and few-shot on summarisation), so comparisons within those two tasks span "
        "two inference configurations. One of these seven results was independently "
        "re-verified from raw model output; the other six were not individually re-checked."
    ),
    "corrections": (
        "Corrections during data collection. Examples that failed to parse were individually "
        "re-queried, and this was not done evenly across techniques. The reported results "
        "include 46 re-queries of 44 examples: zero-shot 24 examples, few-shot CoT 9, CoT 6, "
        "reformulation 3, role prompting 1, structured output 1, and few-shot and "
        "self-consistency none. Of the 42 re-queried examples that had failed, 37 now have a "
        "valid answer and 5 remain failed. Flagged counts should therefore not be compared "
        "directly between techniques. Three re-queries were applied to examples that already "
        "had a valid answer: two returned the same answer, and one (example 48, CoT on "
        "sentiment) returned a different answer and has been restored to its original "
        "prediction. A further 34 logged re-queries (19 for self-consistency, 13 for "
        "zero-shot and 2 for few-shot CoT on question answering) belong to runs that were "
        "later discarded and regenerated in full, and do not affect any reported result. "
        "Finally, on 2026-07-28 the question-answering templates for CoT and few-shot CoT were "
        "edited to add a brevity instruction without a change to the template version number. "
        "Both of these results were regenerated in full on 2026-07-29, so every reported "
        "result uses the edited wording, but the version label alone does not distinguish "
        "the two wordings."
    ),
    "self_consistency": (
        "Self-consistency was regenerated in full. An audit found that its three samples per "
        "example had been sent with the same random seed; in the original sentiment run the "
        "three samples gave the same answer on 97 of the 99 examples for which all three were "
        "logged. All three self-consistency results reported here were regenerated with "
        "seeds 42, 43 and 44 for the three samples, and API or network errors during the "
        "regeneration were retried rather than scored as failures. After regeneration the "
        "three samples agreed on 82 of 100 sentiment examples, 70 of 100 named entity "
        "recognition examples and 86 of 100 paraphrase examples. On paraphrase detection, "
        "agreement was about as high before the change (87 of 98 logged examples), so the "
        "high agreement reflects the model's own consistency at temperature 0.7 and not only "
        "the shared seed."
    ),
    "metrics": (
        "Metric conventions. Sentiment and paraphrase scores are macro F1. TweetEval's "
        "official sentiment metric is macro-averaged recall, and GLUE reports binary F1 for "
        "MRPC, so these scores are not directly comparable to either public leaderboard. "
        "BERTScore uses a bert-base-uncased backbone and is rescaled against a baseline, "
        "which is why its values fall around 0.30 rather than the roughly 0.85 typical of "
        "unrescaled scores; absolute BERTScore values should be treated as indicative."
    ),
    "hallucination": (
        "Summarisation metrics do not detect factual errors. ROUGE-L and BERTScore measure "
        "overlap and similarity with a reference summary, so a fluent summary that states a "
        "wrong fact is not penalised. An informal manual check of a few summaries found "
        "names that the source article does not support. One article refers to the athlete "
        "Sanya Richards-Ross only by her surname; six of the seven techniques (all except "
        "few-shot CoT) called her \"Emma\", the first name of the journalist who interviewed "
        "her. Johnny Manziel, also named only by surname, was called \"Robert\", the first "
        "name of a lawyer quoted in the same article, by few-shot and structured output. "
        "Derek McInnes was called \"Jim\" by CoT and structured output, and the CoT summary "
        "of an article about David Cameron referred to \"Prime Minister Boris Cameron\". The "
        "check was not systematic, so how often such errors occur is not known."
    ),
}


doc = Document()

# ---- base style ----
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)

for level, size, bold in [(1, 16, True), (2, 13, True)]:
    hstyle = doc.styles[f'Heading {level}']
    hstyle.font.name = 'Calibri'
    hstyle.font.size = Pt(size)
    hstyle.font.bold = bold
    hstyle.font.color.rgb = None

sec = doc.sections[0]
sec.left_margin = Inches(1)
sec.right_margin = Inches(1)
sec.top_margin = Inches(1)
sec.bottom_margin = Inches(1)

# ================= TITLE PAGE =================
for _ in range(6):
    doc.add_paragraph()
title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title_p.add_run("A Systematic Benchmark of Prompting Techniques\nAcross NLP Tasks")
run.bold = True
run.font.size = Pt(24)

doc.add_paragraph()
sub_p = doc.add_paragraph()
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub_run = sub_p.add_run("An Empirical Comparison of Eight Prompting Strategies\nAcross Five Natural Language Processing Tasks")
sub_run.italic = True
sub_run.font.size = Pt(14)

for _ in range(4):
    doc.add_paragraph()
meta_p = doc.add_paragraph()
meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta_p.add_run("Independent Research Report\nPrepared for Scholarship Application Submission").font.size = Pt(12)

doc.add_page_break()

# Body section with page numbers in footer
footer = sec.footer
footer_p = footer.paragraphs[0]
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_page_number_field(footer_p)

# ================= ABSTRACT =================
doc.add_heading("Abstract", level=1)
doc.add_paragraph(
    "This study presents a controlled empirical comparison of eight prompting techniques "
    "across five natural language processing tasks, evaluating whether prompting technique "
    "effectiveness varies systematically by task type. Using a single open-weight large "
    "language model (openai/gpt-oss-20b; temperature 0.0, except self-consistency at 0.7; "
    "random seed 42), thirty-eight technique-task combinations were evaluated on 100 "
    "examples each across sentiment classification (TweetEval), named entity recognition "
    "(MultiNERD), abstractive summarisation (XSum), question answering (TriviaQA), and "
    "paraphrase detection (GLUE MRPC). No technique reliably dominated. Reformulation, which "
    "rephrases the task instruction with explicit constraints, scored highest on three tasks "
    "(named entity recognition, question answering, and paraphrase detection) but lowest on "
    "the other two (sentiment classification and summarisation). Few-shot chain-of-thought "
    "scored highest on sentiment classification and summarisation but lowest on named "
    "entity recognition. Zero-shot chain-of-thought and self-consistency did not score "
    "highest on any task, although self-consistency costs three model calls per example. "
    "Most differences are within sampling noise: paired bootstrap 95% confidence intervals "
    "distinguish only 7 of the 33 comparisons between each task's top-scoring technique "
    "and the others, and on no task is the top technique distinguishable from the "
    "runner-up. The rankings should therefore be read as indicative rather than "
    "definitive. The study is limited to English-language tasks, a single model, and a "
    "single random seed; a planned extension to Urdu is not included in this release."
)

# ================= INTRODUCTION =================
doc.add_heading("1. Introduction", level=1)
doc.add_paragraph(
    "Selecting an appropriate prompting technique matters practically: unlike fine-tuning, "
    "prompting requires no additional training data or compute investment beyond inference, "
    "making it the default adaptation strategy for practitioners working with large "
    "pretrained models under cost, latency, or data constraints. However, prompting "
    "techniques vary widely in complexity and inference cost — from a single zero-shot "
    "instruction to self-consistency, which requires multiple independent samples per "
    "input — and it is not obvious a priori which techniques justify their additional cost "
    "on any given task."
)
doc.add_paragraph(
    "Despite the proliferation of prompting techniques in recent years, systematic "
    "cross-task comparison remains limited. Liu et al. (2023), in a survey of prompting "
    "methods, explicitly note that comparisons of prompting techniques across diverse task "
    "types are underrepresented in the literature; most empirical evaluations of a given "
    "technique are conducted on the narrow set of tasks for which that technique was "
    "originally proposed (for example, chain-of-thought on mathematical reasoning "
    "benchmarks), leaving open the question of how techniques compare when tested outside "
    "their original evaluation domain."
)
doc.add_paragraph(
    "This study addresses that gap directly. The research question is: does the "
    "effectiveness of prompting techniques vary systematically by task type, and if so, do "
    "more elaborate, reasoning-oriented techniques reliably outperform simpler ones? To "
    "answer this, eight prompting techniques — zero-shot, few-shot, chain-of-thought, role "
    "prompting, reformulation, self-consistency, structured output, and few-shot "
    "chain-of-thought — were evaluated on five distinct NLP tasks under the same model and "
    "evaluation conditions, with the inference-setting exceptions noted in Limitations: "
    "sentiment classification, named entity "
    "recognition, abstractive summarisation, question answering, and paraphrase detection."
)
doc.add_paragraph(
    "The contribution of this work is a controlled, single-model, eight-technique by "
    "five-task comparison conducted under the same model and evaluation conditions, with every result traceable "
    "to a specific model, prompt template version, and random seed, and every reported "
    "metric independently recomputable from preserved raw model outputs. Rather than "
    "proposing a new prompting technique, this study asks a more fundamental question for "
    "practitioners: given a fixed model and a fixed task, which existing technique is worth "
    "using, and does the answer depend on the task?"
)

# ================= RELATED WORK =================
doc.add_heading("2. Related Work", level=1)
doc.add_paragraph(
    "Liu et al. (2023) provide a comprehensive survey of prompting methods in natural "
    "language processing, cataloguing a wide range of prompting strategies and their "
    "reported applications. Notably, the survey identifies systematic cross-task comparison "
    "of prompting techniques as an open gap in the literature, along with cross-lingual "
    "prompting as an underexplored direction. This study directly addresses the first of "
    "these two gaps by evaluating the same eight techniques across five distinct task types "
    "under the same model and evaluation conditions; the second gap — cross-lingual evaluation — was scoped "
    "during development but is not addressed in this release (see Limitations)."
)
doc.add_paragraph(
    "Wang et al. (2023) introduced self-consistency, showing that sampling multiple "
    "reasoning paths at elevated temperature and taking a majority vote improves "
    "chain-of-thought performance by 17.9 percentage points on the GSM8K mathematical "
    "reasoning benchmark. Their evaluation, however, was restricted to reasoning-oriented "
    "tasks and did not test self-consistency on sentiment classification, named entity "
    "recognition, or free-text generation tasks; the authors themselves acknowledge higher "
    "computational cost as a limitation. This study extends their evaluation to sentiment "
    "classification, named entity recognition, and paraphrase detection (self-consistency "
    "was excluded from question answering and summarisation, where majority voting over "
    "free-text output is undefined), providing evidence on whether the technique's "
    "benefits generalise beyond reasoning tasks."
)
doc.add_paragraph(
    "Brown et al. (2020) demonstrated that few-shot prompting improves performance over "
    "zero-shot prompting with GPT-3, but that the size of this improvement varies "
    "considerably by task — for example, few-shot prompting improved closed-book TriviaQA "
    "performance from 64.3% to 71.2% exact match. This task-dependent effect motivates the "
    "present study's central research question and is consistent with the finding, "
    "reported here, that no single technique dominates across all five tasks evaluated."
)
doc.add_paragraph(
    "Wei et al. (2022) showed that chain-of-thought prompting substantially improves "
    "performance on arithmetic, commonsense, and symbolic reasoning benchmarks, but did not "
    "evaluate the technique on classification or extraction tasks such as sentiment "
    "analysis or named entity recognition. Kojima et al. (2022) similarly showed that a "
    "simple \"let's think step by step\" instruction improves zero-shot reasoning "
    "performance, but restricted evaluation to reasoning benchmarks. This study tests "
    "chain-of-thought prompting, in both zero-shot and few-shot forms, across all five task "
    "types evaluated, including two — sentiment classification and named entity "
    "recognition — that fall outside the reasoning-task domain in which chain-of-thought "
    "was originally validated."
)

# ================= METHODOLOGY =================
doc.add_heading("3. Methodology", level=1)

doc.add_heading("3.1 Model and Inference Settings", level=2)
doc.add_paragraph(
    "All experiments used openai/gpt-oss-20b, accessed via Groq's inference API. "
    "Temperature was fixed at 0.0 for all techniques except self-consistency, which used "
    "temperature 0.7, as in Wang et al. (2023), with three samples per input. Wang et al. "
    "used up to 40 sampled paths, so this is a cost-constrained configuration that may "
    "understate the technique's benefit. A single random seed (42) was fixed across all "
    "experiments, including dataset sampling and few-shot demonstration selection, to "
    "ensure reproducibility; the only exception is that self-consistency's three samples "
    "use seeds 42, 43 and 44, so that they are drawn independently."
)

doc.add_heading("3.2 Prompting Techniques", level=2)
doc.add_paragraph("Eight prompting techniques were evaluated:")
techniques = [
    ("Zero-shot", "a direct task instruction with no examples provided."),
    ("Few-shot", "three in-context demonstrations sampled per instance, with the target "
                 "example always excluded from its own demonstration pool to prevent "
                 "contamination."),
    ("Chain-of-Thought (CoT)", "a \"let's think step by step\" reasoning instruction, "
                                "following Kojima et al. (2022)."),
    ("Role prompting", "the model is assigned a domain-expert persona before receiving the "
                        "task instruction."),
    ("Reformulation", "the task instruction is rephrased with explicit constraints on the "
                       "expected output."),
    ("Self-consistency", "three samples generated at temperature 0.7, each with its own "
                          "random seed, aggregated by "
                          "majority vote, following Wang et al. (2023); excluded from "
                          "question answering and summarisation, where majority voting "
                          "over free-text generation is undefined."),
    ("Structured output", "the model is required to produce its answer in a fixed output "
                           "schema."),
    ("Few-shot CoT", "combines in-context demonstrations with step-by-step reasoning."),
]
for name, desc in techniques:
    p = doc.add_paragraph(style='List Number')
    r = p.add_run(f"{name} — ")
    r.bold = True
    p.add_run(desc)

doc.add_heading("3.3 Tasks and Datasets", level=2)
doc.add_paragraph(
    "Five tasks were evaluated, each sampled to 100 examples with the fixed random seed:"
)
add_table(
    doc,
    ["Task", "Dataset", "Split", "N"],
    [
        ["Sentiment classification", "TweetEval", "test", "100"],
        ["Named entity recognition", "MultiNERD (English)", "test", "100"],
        ["Abstractive summarisation", "XSum", "test", "100"],
        ["Question answering", "TriviaQA (closed-book)", "validation", "100"],
        ["Paraphrase detection", "GLUE MRPC", "test", "100"],
    ],
)
doc.add_paragraph(
    "The sentiment and paraphrase datasets exhibit class imbalance relative to a uniform "
    "label distribution (sentiment: Positive/Neutral/Negative = 18/48/34; paraphrase: "
    "Paraphrase/Not Paraphrase = 76/24), which is relevant when interpreting macro F1 and "
    "accuracy for these two tasks."
)

doc.add_heading("3.4 Evaluation Metrics", level=2)
doc.add_paragraph(
    "Each task was scored using a metric appropriate to its output type, following "
    "standard conventions where applicable: sentiment classification used macro F1 "
    "(TweetEval's official sentiment metric is macro-averaged recall, so these scores are "
    "not directly comparable to the TweetEval leaderboard); named entity recognition used "
    "entity-level F1 requiring exact "
    "span and type match (the CoNLL convention); summarisation used ROUGE-L and BERTScore "
    "with a bert-base-uncased backbone; question answering used exact match and "
    "token-level F1 with article and punctuation normalisation (the SQuAD convention); and "
    "paraphrase detection used macro F1, consistent with this study's standard across all "
    "classification tasks, though this differs from GLUE's official binary-F1 convention "
    "and is not directly comparable to the public MRPC leaderboard without conversion."
)

doc.add_heading("3.5 Output Extraction and Parsing", level=2)
doc.add_paragraph(
    "All model outputs were extracted using a structured <answer> tag contract embedded in "
    "every prompt template, rather than free-text pattern matching. This design choice "
    "ensured consistent, auditable parsing across all eight techniques regardless of how "
    "verbose or structured a given technique's raw output was — a chain-of-thought "
    "response, for example, could contain substantial reasoning text before its final "
    "answer, and the tag contract allowed the answer to be extracted deterministically "
    "without relying on heuristics that might behave differently across techniques. Parse "
    "failures — a missing tag, an empty response, or a content-filter refusal — were "
    "counted as incorrect predictions in every metric rather than excluded from the "
    "evaluation set, and per-technique failure rates (\"flagged\" counts) are reported "
    "alongside every score in the Results section."
)

doc.add_heading("3.6 Pipeline Integrity and Reproducibility", level=2)
doc.add_paragraph(
    "The evaluation pipeline underwent iterative internal audit throughout development. "
    "Measurement validity — including metric computation correctness, prompt template "
    "consistency, and demonstration-sampling integrity — was verified iteratively during "
    "data collection; corrections made after some results existed are disclosed in "
    "Limitations. Every reported result is traceable to a specific model name, prompt "
    "template version, normaliser version, and random seed, recorded per experiment; raw "
    "model predictions for every example are preserved, allowing every reported metric to "
    "be independently recomputed from source data."
)

# ================= RESULTS =================
doc.add_heading("4. Results", level=1)
doc.add_paragraph(
    "Thirty-eight of thirty-eight planned English-language experiments were completed "
    "(eight techniques across five tasks, with self-consistency excluded from question "
    "answering and summarisation). Tables 1 through 5 report the complete results for each "
    "task. Techniques are ranked by the task's primary metric; techniques with identical "
    "scores are listed alphabetically. \"Flagged\" indicates the number of examples, out "
    "of 100, for which a parse failure occurred and the prediction was counted as "
    "incorrect. The 95% confidence intervals come from the paired bootstrap described in "
    "Section 4.6."
)

doc.add_heading("4.1 Sentiment Classification (Macro F1)", level=2)
add_table(doc, *result_table_rows("sentiment"))
doc.add_paragraph(
    "Few-shot CoT, which combines demonstrations with reasoning, scored highest (0.7159), "
    "but its lead over few-shot prompting (0.6924) is within sampling noise; the bootstrap "
    "distinguishes it only from self-consistency and reformulation (Section 4.6). CoT alone "
    "(0.6577) scored slightly below zero-shot (0.6663). Self-consistency, despite three "
    "model calls per example, scored below zero-shot (0.6309), and reformulation scored "
    "lowest of the eight techniques (0.6047)."
)

doc.add_heading("4.2 Named Entity Recognition (Entity-Level F1)", level=2)
add_table(doc, *result_table_rows("ner"))
doc.add_paragraph(
    "Seven of the eight techniques scored between 0.748 and 0.769. Reformulation scored "
    "highest despite four flagged examples, but its lead over few-shot prompting is within "
    "sampling noise. Self-consistency and zero-shot tied at exactly 0.7500. Few-shot CoT "
    "scored lowest (0.6957) and is the only technique the bootstrap distinguishes from "
    "reformulation; one possible reading is that combining demonstrations with reasoning "
    "added noise to entity extraction rather than improving precision."
)

doc.add_heading("4.3 Abstractive Summarisation (ROUGE-L / BERTScore)", level=2)
add_table(doc, *result_table_rows("summarisation"))
doc.add_paragraph(
    "All techniques scored well below the fine-tuned PEGASUS baseline (approximately 0.40 "
    "ROUGE-L), consistent with expectations for zero/few-shot prompting versus fine-tuned "
    "models. All seven techniques fell within 0.010 ROUGE-L of each other (0.1709 to "
    "0.1801), suggesting that prompting strategy has limited impact on summarisation "
    "scores relative to the underlying model's capability. Few-shot CoT ranked first on "
    "ROUGE-L, 0.0001 ahead of structured output, while zero-shot had the highest BERTScore; "
    "reformulation was lowest on both metrics. These metrics also do not detect factual "
    "errors in the summaries (see Limitations)."
)

doc.add_heading("4.4 Question Answering (Exact Match / Token F1)", level=2)
add_table(doc, *result_table_rows("qa"))
doc.add_paragraph(
    "Reformulation scored highest on exact match (0.59) and token F1, four percentage points ahead of "
    "few-shot, role and structured output (0.55 each); this lead is within sampling noise, "
    "and the bootstrap distinguishes reformulation only from zero-shot (0.51), which "
    "scored lowest. CoT (0.53) and few-shot CoT (0.52) scored below few-shot, role and "
    "structured output on this closed-book factual task, and above zero-shot."
)

doc.add_heading("4.5 Paraphrase Detection (Macro F1)", level=2)
add_table(doc, *result_table_rows("paraphrase"))
doc.add_paragraph(
    "Reformulation scored highest on paraphrase detection (0.7472), followed by role "
    "prompting (0.7335) and self-consistency (0.7270), but its lead over role prompting is "
    "within sampling noise. Structured output (0.6495) and CoT (0.6464) scored lowest, and "
    "these are the only two techniques the bootstrap distinguishes from reformulation. "
    "Reformulation's result did not carry over to sentiment classification, the other "
    "classification task, where it scored lowest."
)

doc.add_heading("4.6 Cross-Task Synthesis", level=2)
doc.add_paragraph(
    "No technique reliably dominated across the five tasks, and most differences are within "
    "sampling noise. The top-scoring technique changed with the task: reformulation on "
    "named entity recognition, question answering and paraphrase detection, and few-shot "
    "CoT on sentiment classification and summarisation (ROUGE-L). Each of these two "
    "techniques also scored lowest somewhere: reformulation on sentiment classification "
    "and on both summarisation metrics, and few-shot CoT on named entity recognition. "
    "Zero-shot CoT never scored highest, and ranked last on paraphrase detection. "
    "Self-consistency, which requires three model calls per example, never scored highest: "
    "it ranked seventh of eight on sentiment classification, tied with zero-shot in the "
    "middle of the named entity recognition table, and third of eight on paraphrase "
    "detection. Simple prompting was competitive throughout: few-shot prompting ranked "
    "second on sentiment classification, named entity recognition and question answering "
    "(tied on question answering), and zero-shot had the highest summarisation BERTScore."
)
doc.add_paragraph(
    "These rankings carry substantial uncertainty. A paired bootstrap (1,000 resamples of "
    "the 100 examples per task, with every technique scored on the same resampled "
    "examples) compared each task's top-scoring technique with each of the others, 33 "
    "comparisons in all. Only 7 were distinguishable at the 95% level: few-shot CoT over "
    "self-consistency and over reformulation on sentiment classification; reformulation "
    "over few-shot CoT on named entity recognition; few-shot CoT over CoT on summarisation, "
    "with a lower bound of 0.0001; reformulation over zero-shot on question answering; and "
    "reformulation over structured output and over CoT on paraphrase detection. On no task "
    "was the top-scoring technique distinguishable from the runner-up; in particular, "
    "reformulation's lead was not distinguishable on any of the three tasks it led. No "
    "correction for multiple comparisons was applied, so even these seven differences "
    "should be read cautiously. Full intervals are provided with the project materials."
)
doc.add_paragraph(
    "Read together, the results are consistent with the possibility that, for tasks with "
    "well-defined objectives, a clearly specified instruction matters as much as reasoning "
    "depth or demonstration count. They do not establish this, because the leading "
    "technique's advantage is never distinguishable from the runner-up and it reverses on "
    "other tasks."
)

# ================= DISCUSSION =================
doc.add_heading("5. Discussion", level=1)
doc.add_paragraph(
    "Reasoning-oriented techniques did not consistently outperform simpler alternatives. "
    "Zero-shot CoT never ranked first on any task, and few-shot CoT ranked first on "
    "sentiment classification and summarisation (ROUGE-L) but last on named entity "
    "recognition. This mixed pattern invites explanation. One plausible interpretation is "
    "that chain-of-thought and self-consistency were designed and validated primarily on "
    "tasks requiring multi-step deductive or arithmetic reasoning, where an intermediate "
    "reasoning trace can meaningfully constrain and improve the final answer. The five "
    "tasks evaluated here are largely tasks with a single well-defined answer that does not "
    "require multi-step derivation: classifying the sentiment of a sentence, extracting "
    "named entities, or identifying a paraphrase pair does not obviously benefit from an "
    "intermediate reasoning trace in the way that a multi-step arithmetic problem does. A "
    "second, model-specific factor is that gpt-oss-20b already reasons internally before "
    "every answer, which likely narrows the room for an explicit reasoning instruction to "
    "help (see Limitations). Wei et al. (2022) and Kojima et al. (2022) validated their "
    "techniques on reasoning benchmarks; the results here do not contradict their findings "
    "so much as suggest that chain-of-thought's benefit depends on the task and the model."
)
doc.add_paragraph(
    "Reformulation is the most uneven technique in this study. It scored highest on named "
    "entity recognition, question answering and paraphrase detection, but lowest on "
    "sentiment classification and on both summarisation metrics, and none of its leads is "
    "distinguishable from the runner-up. Where it led, it required no demonstrations, no "
    "additional sampling, and no reasoning trace, only a rephrased instruction with "
    "explicit output constraints. One possible explanation is that some failures of other "
    "techniques stem from output ambiguity rather than from the model's task capability: "
    "an explicit, tightly constrained instruction may reduce uncertainty about what form "
    "the answer should take. Its largest margin was on question answering, where the "
    "expected output (a short factual answer) is easy to specify precisely. Its weak "
    "results on sentiment classification and summarisation show that the same kind of "
    "rewording can also hurt, so this explanation remains a hypothesis rather than a "
    "finding."
)
doc.add_paragraph(
    "These results also complicate a straightforward reading of Wang et al. (2023). "
    "Self-consistency, despite requiring three model calls per example, never scored "
    "highest: it ranked seventh of eight on sentiment classification, tied with zero-shot "
    "on named entity recognition, and third on paraphrase detection. Two explanations are "
    "possible, and this study cannot separate them. The first is task structure: majority "
    "voting over three samples offers limited value when errors come from instruction "
    "ambiguity or output formatting rather than from inconsistent reasoning, and the three "
    "samples agreed on most examples (82 of 100 on sentiment classification, 70 on named "
    "entity recognition, 86 on paraphrase detection). The second is temperature: "
    "self-consistency samples at temperature 0.7, while every other technique runs at "
    "0.0, so each individual sample is noisier than a single greedy answer, and voting "
    "over only three samples may not recover that loss. Wang et al. used up to 40 "
    "samples, so this three-sample configuration may understate the technique's benefit."
)
doc.add_paragraph(
    "Taken together, these results support cautious, task-specific advice rather than a "
    "single recommendation. Under a fixed model, the choice of technique changed the score "
    "on each task, but by margins that 100 examples per task mostly cannot resolve, and the "
    "technique that led on one task was often among the weakest on another. Practitioners "
    "should therefore test a small set of inexpensive candidates, such as zero-shot, "
    "few-shot and a reformulated instruction, on their own task before paying for more "
    "expensive techniques. This advice is offered as a pattern observed under a single "
    "model, a single seed and five tasks, not as a general claim."
)

# ================= LIMITATIONS =================
doc.add_heading("6. Limitations", level=1)
doc.add_paragraph(
    "This study was conducted using a single model (openai/gpt-oss-20b, via Groq) and a "
    "single random seed (42); no cross-model comparison or run-to-run variance data is "
    "available. The paired bootstrap confidence intervals reported in Section 4 capture "
    "only the uncertainty from sampling 100 examples per task; they do not capture "
    "run-to-run variation or variation across models, and no correction for multiple "
    "comparisons was applied."
)
doc.add_paragraph(
    "This release is scoped to English-language tasks only. A cross-lingual extension to "
    "Urdu (Roman Urdu sentiment classification and Urdu named entity recognition) was "
    "scoped during development, and the corresponding datasets were downloaded and "
    "processed, but prompt templates and experiments for these tasks were not completed in "
    "time for this release. Urdu evaluation is documented as future work."
)
doc.add_paragraph(LIMITATIONS["model"])
doc.add_paragraph(LIMITATIONS["inference"])
doc.add_paragraph(LIMITATIONS["corrections"])
doc.add_paragraph(LIMITATIONS["self_consistency"])
doc.add_paragraph(LIMITATIONS["metrics"])
doc.add_paragraph(LIMITATIONS["hallucination"])
doc.add_paragraph(
    "Finally, the sentiment and paraphrase datasets exhibit class imbalance relative to a "
    "uniform label distribution (sentiment: Positive/Neutral/Negative = 18/48/34; "
    "paraphrase: Paraphrase/Not Paraphrase = 76/24), which should be considered when "
    "interpreting macro F1 and accuracy for these two tasks."
)

# ================= CONCLUSION =================
doc.add_heading("7. Conclusion", level=1)
doc.add_paragraph(
    "This study evaluated eight prompting techniques across five English NLP tasks with one "
    "model, addressing a gap in the literature around systematic cross-task comparison of "
    "prompting strategies. The central finding is that no technique reliably dominated and "
    "that most differences between techniques are within sampling noise at 100 examples "
    "per task. Reasoning-oriented techniques did not reliably outperform simpler ones: "
    "zero-shot chain-of-thought never scored highest, few-shot chain-of-thought scored "
    "highest on two tasks but lowest on a third, and self-consistency, at three model calls "
    "per example, never scored highest. Reformulation, one of the simplest techniques, "
    "scored highest on three tasks (named entity recognition, question answering and "
    "paraphrase detection) but lowest on the other two (sentiment classification and "
    "summarisation), and none of its leads is statistically distinguishable from the "
    "runner-up."
)
doc.add_paragraph(
    "Future work should extend this comparison in two directions: completing the "
    "cross-lingual arm of this study, for which Urdu datasets have already been processed "
    "but prompt templates and experiments remain outstanding, and strengthening the "
    "statistical evidence, through larger evaluation sets, multi-seed replication and "
    "additional models, since the bootstrap intervals reported here cannot separate most "
    "techniques at 100 examples per task."
)
doc.add_paragraph(
    "For practitioners choosing a prompting strategy under cost or latency constraints, "
    "the practical lesson is to validate on the task at hand rather than adopt any "
    "technique by default. Inexpensive options (zero-shot, few-shot and a carefully "
    "reformulated instruction) were competitive with the more elaborate techniques here, "
    "but which of them did best depended on the task."
)

# ================= REFERENCES =================
doc.add_heading("References", level=1)
refs = [
    "Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J. D., Dhariwal, P., "
    "Neelakantan, A., Shyam, P., Sastry, G., Askell, A., Agarwal, S., Herbert-Voss, A., "
    "Krueger, G., Henighan, T., Child, R., Ramesh, A., Ziegler, D., Wu, J., Winter, C., "
    "... Amodei, D. (2020). Language models are few-shot learners. Advances in Neural "
    "Information Processing Systems, 33, 1877-1901.",

    "Kojima, T., Gu, S. S., Reid, M., Matsuo, Y., & Iwasawa, Y. (2022). Large language "
    "models are zero-shot reasoners. Advances in Neural Information Processing Systems, "
    "35, 22199-22213.",

    "Liu, P., Yuan, W., Fu, J., Jiang, Z., Hayashi, H., & Neubig, G. (2023). Pre-train, "
    "prompt, and predict: A systematic survey of prompting methods in natural language "
    "processing. ACM Computing Surveys, 55(9), 1-35.",

    "Wang, X., Wei, J., Schuurmans, D., Le, Q., Chi, E., Narang, S., Chowdhery, A., & "
    "Zhou, D. (2023). Self-consistency improves chain of thought reasoning in language "
    "models. In Proceedings of the International Conference on Learning Representations "
    "(ICLR 2023).",

    "Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi, E., Le, Q., "
    "& Zhou, D. (2022). Chain-of-thought prompting elicits reasoning in large language "
    "models. Advances in Neural Information Processing Systems, 35, 24824-24837.",
]
for ref in refs:
    p = doc.add_paragraph(ref)
    p.paragraph_format.left_indent = Inches(0.5)
    p.paragraph_format.first_line_indent = Inches(-0.5)

doc.save("Prompting_Technique_Benchmark_Paper.docx")
print("Saved: Prompting_Technique_Benchmark_Paper.docx")
