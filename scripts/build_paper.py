# One-off script to assemble the scholarship-application paper as a .docx
# from methodology.md, results_summary.md, and baselines.md. Not part of the
# experiment pipeline — run manually, not imported elsewhere.

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
    "language model (openai/gpt-oss-20b) under fixed inference settings (temperature 0.0, "
    "except self-consistency at 0.7; random seed 42), thirty-eight technique-task "
    "combinations were evaluated across sentiment classification (TweetEval), named entity "
    "recognition (MultiNERD), abstractive summarisation (XSum), question answering "
    "(TriviaQA), and paraphrase detection (GLUE MRPC). Results show that reasoning-oriented "
    "techniques — chain-of-thought and self-consistency — do not reliably outperform simpler "
    "techniques such as zero-shot, few-shot, or reformulation, despite substantially higher "
    "inference cost in the case of self-consistency. Reformulation, which rephrases the task "
    "instruction with explicit constraints, was the strongest technique on three of five "
    "tasks (named entity recognition, question answering, and paraphrase detection) but the "
    "near the bottom on the other two (second-to-last on sentiment classification and last "
    "on summarisation ROUGE-L), so its "
    "advantage is task-dependent. This suggests that, "
    "for tasks with well-defined objectives, instruction clarity may matter more than "
    "reasoning depth or demonstration count. The study is scoped to English-language tasks, "
    "a single model, and a single random seed. Paired bootstrap 95% confidence intervals "
    "show that most differences between techniques within a task are not statistically "
    "distinguishable at 100 examples per task, so rankings should be read as indicative "
    "rather than definitive. A planned cross-lingual extension to Urdu was scoped during "
    "development but is not included in this release."
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
    "five-task comparison conducted under matched conditions, with every result traceable "
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
    "under matched conditions; the second gap — cross-lingual evaluation — was scoped "
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
    "data collection and refinement, with corrections disclosed in Limitations where they "
    "affected already-collected results. Every reported result is traceable to a specific model name, prompt "
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
    "task. \"Flagged\" indicates the number of examples, out of 100, for which a parse "
    "failure occurred and the prediction was counted as incorrect."
)

doc.add_heading("4.1 Sentiment Classification (Macro F1)", level=2)
add_table(
    doc,
    ["Technique", "Macro F1", "95% CI", "Flagged"],
    [
        ["Few-shot CoT", "0.7159", "0.618–0.800", "0"],
        ["Few-shot", "0.6924", "0.595–0.780", "0"],
        ["Role", "0.6673", "0.573–0.750", "0"],
        ["Zero-shot", "0.6663", "0.568–0.758", "0"],
        ["Structured output", "0.6583", "0.567–0.745", "0"],
        ["CoT", "0.6577", "0.563–0.746", "0"],
        ["Reformulation", "0.6047", "0.504–0.699", "0"],
        ["Self-consistency", "0.6015", "0.499–0.693", "0"],
    ],
)
doc.add_paragraph(
    "Combining demonstrations with reasoning (few-shot CoT) produced the strongest result. "
    "CoT alone did not outperform zero-shot, suggesting explicit reasoning adds limited "
    "value for sentiment classification without accompanying examples. Self-consistency, "
    "despite requiring three times the inference cost, underperformed simple zero-shot "
    "prompting."
)

doc.add_heading("4.2 Named Entity Recognition (Entity-Level F1)", level=2)
add_table(
    doc,
    ["Technique", "Entity F1", "95% CI", "Flagged"],
    [
        ["Reformulation", "0.7692", "0.694–0.834", "4"],
        ["Few-shot", "0.7573", "0.689–0.814", "0"],
        ["Self-consistency", "0.7539", "0.693–0.810", "0"],
        ["CoT", "0.7524", "0.691–0.808", "1"],
        ["Structured output", "0.7516", "0.680–0.815", "2"],
        ["Zero-shot", "0.7500", "0.680–0.814", "2"],
        ["Role", "0.7483", "0.678–0.813", "3"],
        ["Few-shot CoT", "0.6957", "0.612–0.776", "0"],
    ],
)
doc.add_paragraph(
    "Performance clustered tightly across most techniques (0.75-0.77), with few-shot CoT "
    "as a notable underperformer — the combination of demonstrations and reasoning appears "
    "to introduce noise for extraction tasks rather than improving precision."
)

doc.add_heading("4.3 Abstractive Summarisation (ROUGE-L / BERTScore)", level=2)
add_table(
    doc,
    ["Technique", "ROUGE-L", "95% CI", "BERTScore F1", "Flagged"],
    [
        ["Few-shot CoT", "0.1801", "0.168–0.193", "0.3044", "0"],
        ["Structured output", "0.1800", "0.162–0.196", "0.2997", "6"],
        ["Zero-shot", "0.1774", "0.163–0.192", "0.3105", "0"],
        ["Few-shot", "0.1761", "0.163–0.190", "0.3020", "0"],
        ["Role", "0.1739", "0.158–0.188", "0.3032", "0"],
        ["CoT", "0.1715", "0.159–0.184", "0.3056", "0"],
        ["Reformulation", "0.1709", "0.155–0.186", "0.2977", "0"],
    ],
)
doc.add_paragraph(
    "All techniques scored well below the fine-tuned PEGASUS baseline (approximately 0.40 "
    "ROUGE-L), consistent with expectations for zero/few-shot prompting versus fine-tuned "
    "models. Scores clustered closely across techniques, suggesting prompting strategy has "
    "limited impact on abstractive summarisation quality relative to the underlying "
    "model's capability."
)

doc.add_heading("4.4 Question Answering (Exact Match / Token F1)", level=2)
add_table(
    doc,
    ["Technique", "Exact Match", "95% CI", "Token F1", "Flagged"],
    [
        ["Reformulation", "0.59", "0.50–0.68", "0.6453", "0"],
        ["Few-shot", "0.55", "0.46–0.64", "0.6296", "0"],
        ["Role", "0.55", "0.46–0.64", "0.6131", "0"],
        ["Structured output", "0.55", "0.46–0.64", "0.5999", "2"],
        ["CoT", "0.53", "0.43–0.63", "0.5894", "1"],
        ["Few-shot CoT", "0.52", "0.43–0.62", "0.5963", "1"],
        ["Zero-shot", "0.51", "0.42–0.61", "0.5777", "2"],
    ],
)
doc.add_paragraph(
    "Reformulation performed best on QA, suggesting that rephrasing the instruction with "
    "explicit constraints helps the model produce more precise short-answer outputs. "
    "Reasoning-based techniques (CoT, few-shot CoT) did not outperform simpler approaches "
    "on this closed-book factual QA task."
)

doc.add_heading("4.5 Paraphrase Detection (Macro F1)", level=2)
add_table(
    doc,
    ["Technique", "Macro F1", "95% CI", "Flagged"],
    [
        ["Reformulation", "0.7472", "0.647–0.840", "0"],
        ["Role", "0.7335", "0.631–0.826", "1"],
        ["Self-consistency", "0.7143", "0.616–0.802", "0"],
        ["Zero-shot", "0.7040", "0.603–0.790", "1"],
        ["Few-shot", "0.6970", "0.596–0.785", "2"],
        ["Few-shot CoT", "0.6923", "0.597–0.787", "0"],
        ["Structured output", "0.6495", "0.549–0.740", "1"],
        ["CoT", "0.6464", "0.543–0.741", "1"],
    ],
)
doc.add_paragraph(
    "Reformulation again performed best, reinforcing a pattern across tasks: explicit "
    "rephrasing of the instruction outperforms both minimal prompting and reasoning-heavy "
    "techniques for binary classification-style judgments, though this did not extend to "
    "sentiment classification, the other classification task, where reformulation ranked "
    "second-to-last."
)

doc.add_heading("4.6 Cross-Task Synthesis", level=2)
doc.add_paragraph(
    "Across all five tasks, a consistent pattern emerges: elaborate reasoning-oriented "
    "techniques (chain-of-thought, self-consistency) do not reliably outperform simpler "
    "techniques (zero-shot, few-shot, reformulation) on this model, and in several cases "
    "underperform despite substantially higher computational cost. Self-consistency, which "
    "requires three times the inference calls, was never the best-performing technique on "
    "any task, and was the lowest-scoring technique on sentiment classification (0.6015, "
    "narrowly below reformulation at 0.6047). Reformulation — simply rephrasing the instruction with explicit "
    "constraints — was the strongest technique on three of five tasks (NER, QA, paraphrase "
    "detection) but near the bottom on the other two (second-to-last on sentiment "
    "classification and last on summarisation ROUGE-L), so its advantage is task-dependent."
)
doc.add_paragraph(
    "These rankings carry substantial uncertainty. A paired bootstrap (1,000 resamples of "
    "the 100 examples per task, with every technique scored on the same resampled "
    "examples) found that only 8 of the 33 comparisons between each task's best technique "
    "and the others were statistically distinguishable at the 95% level: few-shot CoT over "
    "reformulation and self-consistency on sentiment classification; reformulation over "
    "structured output and CoT on paraphrase detection, over few-shot CoT on named entity "
    "recognition, and over zero-shot on question answering; and few-shot CoT over CoT on "
    "summarisation, by a margin of 0.0001 at the lower bound. Reformulation's lead over the "
    "second-ranked technique was not statistically distinguishable on any of the three "
    "tasks it led. No correction for multiple comparisons was applied, so even these eight "
    "differences should be read cautiously. Full intervals are in "
    "outputs/tables/bootstrap_ci.csv."
)
doc.add_paragraph(
    "This suggests that for tasks with well-defined, unambiguous objectives, prompt "
    "clarity and instruction precision may matter more than reasoning depth or "
    "demonstration count — a finding that has practical implications for practitioners "
    "choosing prompting strategies under compute or latency constraints."
)

# ================= DISCUSSION =================
doc.add_heading("5. Discussion", level=1)
doc.add_paragraph(
    "Reasoning-oriented techniques did not consistently outperform simpler alternatives. "
    "Zero-shot CoT never ranked first on any task, and few-shot CoT ranked first on "
    "sentiment and summarisation (ROUGE-L) but last on NER. This mixed pattern invites "
    "explanation. One "
    "plausible interpretation is that chain-of-thought and self-consistency were designed "
    "and validated primarily on tasks requiring multi-step deductive or arithmetic "
    "reasoning — domains in which an intermediate reasoning trace can meaningfully "
    "constrain and improve the final answer. The five tasks evaluated here, by contrast, "
    "are largely tasks with a single well-defined correct answer that does not require "
    "multi-step derivation: classifying the sentiment of a sentence, extracting named "
    "entities, or identifying a paraphrase pair does not obviously benefit from an "
    "intermediate reasoning trace in the way that a multi-step arithmetic problem does. "
    "Wei et al. (2022) and Kojima et al. (2022) both validated their respective techniques "
    "exclusively on reasoning benchmarks; the results here do not contradict their "
    "findings so much as they clarify the boundary of where those findings apply — "
    "chain-of-thought's benefit appears to be conditional on task structure rather than "
    "universal."
)
doc.add_paragraph(
    "The performance of reformulation is a more direct point of interest. Reformulation "
    "was the strongest technique on three of five tasks (named entity recognition, question "
    "answering, and paraphrase detection) but near the bottom on the other two "
    "(second-to-last on sentiment classification and last on summarisation ROUGE-L), so its "
    "advantage is task-dependent. Where "
    "it led, it required no demonstrations, no additional sampling, and no reasoning trace "
    "— only a rephrased instruction with explicit output constraints. A plausible "
    "explanation is that many of "
    "the failures observed with other techniques were less about the model's underlying "
    "task capability and more about output ambiguity: an explicit, tightly constrained "
    "instruction may reduce the model's uncertainty about what form its answer should "
    "take, independent of whether the model reasons about the task at all. This is "
    "consistent with the observation that reformulation's advantage was strongest on QA "
    "and paraphrase detection — tasks where the correct output format (a short factual "
    "answer; a binary label) is easy to specify precisely, but where free-form model "
    "responses can otherwise drift into hedged, verbose, or ambiguously formatted answers."
)
doc.add_paragraph(
    "This finding also complicates a straightforward reading of Wang et al. (2023): "
    "self-consistency, despite requiring three times the inference cost of a single-sample "
    "technique, was never the best-performing technique on any of the five tasks evaluated "
    "here, and was the lowest-scoring technique on sentiment classification. Because self-"
    "consistency was validated by its original authors on mathematical reasoning tasks "
    "where multiple independent reasoning paths can meaningfully disagree and be resolved "
    "by majority vote, its lack of benefit here is consistent with the same task-structure "
    "explanation offered above — majority voting over three samples offers limited value "
    "when the underlying source of error is not reasoning inconsistency but instruction "
    "ambiguity or output formatting variance."
)
doc.add_paragraph(
    "Taken together, these results suggest a practical heuristic: for tasks with a "
    "well-defined, unambiguous objective, practitioners may achieve better results, at "
    "lower inference cost, by investing effort in instruction clarity rather than adopting "
    "the most sophisticated or most expensive available technique. This heuristic is "
    "offered cautiously, as a pattern observed under a single model, single seed, and five "
    "tasks, rather than a general theoretical claim."
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
doc.add_paragraph(
    "Seven of the thirteen question-answering and summarisation results (zero-shot, "
    "few-shot, role and structured output on QA; zero-shot, few-shot and structured output "
    "on summarisation) were generated prior to the tuning of a reasoning-efficiency inference setting, finalised on "
    "2026-07-28. One of these seven results was independently re-verified from raw model "
    "output and confirmed accurate; the remaining six were not individually re-checked, "
    "though no quality issues were observed in this group during review. This is disclosed "
    "here rather than silently corrected, in keeping with this study's broader commitment "
    "to auditable, traceable results."
)
doc.add_paragraph(
    "The BERTScore metric used for summarisation evaluation uses a bert-base-uncased "
    "backbone; absolute BERTScore values should be treated as indicative rather than "
    "calibrated against stronger, more recent backbone models."
)
doc.add_paragraph(
    "Model and inference caveats. openai/gpt-oss-20b is a reasoning model that produces "
    "hidden internal reasoning before its visible answer. These reasoning tokens count "
    "against the generation limit. As a result, every technique, including zero-shot, "
    "involves some internal reasoning, which likely narrows the measurable benefit of "
    "explicit chain-of-thought prompting. It is also the most likely cause of the "
    "truncated, empty responses that make up 21 of the 30 remaining parse failures. To "
    "limit truncation, question answering and summarisation were run with the provider's "
    "reasoning_effort parameter set to \"low\", while the other three tasks used the "
    "provider default. Seven of the thirteen QA and summarisation results were generated "
    "before this setting was introduced, so comparisons within those two tasks span two "
    "inference configurations. Examples that failed to parse were individually "
    "re-queried: 70 re-queries were logged during data collection, of which 47 produced a "
    "valid answer, and all remaining failures are scored as incorrect. Re-queries were not "
    "applied uniformly across techniques, so flagged counts should not be compared "
    "directly between techniques. Self-consistency results were regenerated in full "
    "after an audit found that all three samples for each example had been sent with the "
    "same random seed, which made them near-identical; each sample now uses its own seed "
    "(42, 43 and 44), and API or network errors during this rerun were retried rather "
    "than scored as failures. One example that had already produced a "
    "valid answer and was re-queried in error has been restored to its original "
    "prediction. Three failures caused by network errors rather than model output are "
    "also scored as incorrect. BERTScore values are rescaled against the bert-base-uncased "
    "baseline (rescale_with_baseline=True), which is why they fall around 0.30 rather than "
    "the roughly 0.85 typical of unrescaled scores."
)
doc.add_paragraph(
    "Paraphrase detection is reported using macro F1, consistent with this study's "
    "evaluation convention across all classification tasks, rather than GLUE's official "
    "binary-F1 convention. As a result, paraphrase scores reported here are not directly "
    "comparable to the public MRPC leaderboard without conversion."
)
doc.add_paragraph(
    "Finally, the sentiment and paraphrase datasets exhibit class imbalance relative to a "
    "uniform label distribution (sentiment: Positive/Neutral/Negative = 18/48/34; "
    "paraphrase: Paraphrase/Not Paraphrase = 76/24), which should be considered when "
    "interpreting macro F1 and accuracy for these two tasks."
)

# ================= CONCLUSION =================
doc.add_heading("7. Conclusion", level=1)
doc.add_paragraph(
    "This study evaluated eight prompting techniques across five NLP tasks under the same "
    "model and evaluation conditions, addressing a gap in the literature around systematic "
    "cross-task comparison of prompting strategies. The central finding is that "
    "reasoning-oriented techniques — chain-of-thought and self-consistency — do not "
    "reliably outperform simpler techniques, and in several cases underperform despite "
    "meaningfully higher inference cost; self-consistency, which requires three times the "
    "inference calls of a single-sample technique, was never the best-performing technique "
    "on any of the five tasks evaluated. Reformulation, one of the simplest and cheapest "
    "techniques evaluated, was the strongest technique on three of five tasks (named entity "
    "recognition, question answering, and paraphrase detection) but near the bottom "
    "on the other two (second-to-last on sentiment classification and last on "
    "summarisation ROUGE-L), so its advantage is "
    "task-dependent, suggesting that instruction clarity may matter more than reasoning depth or "
    "demonstration count for tasks with well-defined objectives."
)
doc.add_paragraph(
    "Future work should extend this comparison along two directions: completing the "
    "cross-lingual arm of this study, for which Urdu datasets have already been processed "
    "but prompt templates and experiments remain outstanding, and strengthening the "
    "statistical evidence — larger evaluation sets, multi-seed replication, and additional "
    "models — since the bootstrap intervals reported here cannot separate most techniques "
    "at 100 examples per task."
)
doc.add_paragraph(
    "For practitioners choosing a prompting strategy under real-world cost or latency "
    "constraints, these results offer a concrete, if provisional, recommendation: a "
    "carefully reformulated instruction is worth including among the candidates tested; it "
    "was the best technique on three tasks but near the bottom on the other two, so it should be validated "
    "per task rather than adopted by default."
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
