import csv, os, glob, ast
from src.metric_engine import compute_metrics

os.makedirs('outputs/results', exist_ok=True)
path = 'outputs/results/results_master.csv'

all_columns = [
    'experiment_id', 'date', 'model', 'technique', 'task', 'language',
    'token_input_avg', 'token_output_avg', 'prompt_version', 'normaliser_version',
    'random_seed', 'flagged_count', 'notes',
    'macro_f1', 'accuracy', 'entity_f1', 'precision', 'recall',
    'rouge_l', 'bert_f1', 'exact_match', 'token_f1'
]

results = []
for pred_file in sorted(glob.glob('outputs/predictions/*.csv')):
    name = os.path.basename(pred_file).replace('.csv', '')

    with open(pred_file, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    if not rows:
        continue

    # Detect task and language from filename
    if 'urdu_sentiment' in name:
        task = 'urdu_sentiment'
        language = 'urdu'
    elif 'urdu_ner' in name:
        task = 'urdu_ner'
        language = 'urdu'
    elif 'sentiment' in name:
        task = 'sentiment'
        language = 'english'
    elif 'ner' in name:
        task = 'ner'
        language = 'english'
    elif 'summarisation' in name:
        task = 'summarisation'
        language = 'english'
    elif 'qa' in name:
        task = 'qa'
        language = 'english'
    elif 'paraphrase' in name:
        task = 'paraphrase'
        language = 'english'
    else:
        print(f'Skipping unknown file: {name}')
        continue

    # Detect technique by removing task and language suffix
    technique = name
    for suffix in [f'_{task}_english', f'_{task}_urdu', f'_{task}']:
        technique = technique.replace(suffix, '')

    # Build predictions and references
    preds, refs = [], []
    for r in rows:
        pred = r['prediction']
        ref = r['reference']
        if task in ('ner', 'urdu_ner'):
            try:
                pred = ast.literal_eval(pred)
                ref = ast.literal_eval(ref)
            except:
                pred = []
        preds.append(pred)
        refs.append(ref)

    # Compute metrics
    try:
        metrics = compute_metrics(task, preds, refs)
    except Exception as e:
        print(f'Metrics error for {name}: {e}')
        metrics = {}

    flagged = sum(1 for r in rows if r.get('status') != 'ok')
    tokens_in = [float(r['input_tokens']) for r in rows
                 if r.get('input_tokens', '0') not in ('0', '')]
    tokens_out = [float(r['output_tokens']) for r in rows
                  if r.get('output_tokens', '0') not in ('0', '')]

    row = {col: '' for col in all_columns}
    row['experiment_id'] = name
    row['date'] = '2026-07-21'
    row['model'] = 'openai/gpt-oss-20b'
    row['technique'] = technique
    row['task'] = task
    row['language'] = language
    row['token_input_avg'] = round(sum(tokens_in)/len(tokens_in), 1) if tokens_in else 0
    row['token_output_avg'] = round(sum(tokens_out)/len(tokens_out), 1) if tokens_out else 0
    row['prompt_version'] = '1.0'
    row['normaliser_version'] = '3.0'
    row['random_seed'] = 42
    row['flagged_count'] = flagged
    row['notes'] = 'rebuilt from predictions'
    row.update(metrics)
    results.append(row)
    print(f'Rebuilt: {technique:20} {task:12} {language} rows={len(rows)} flagged={flagged}')

with open(path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=all_columns)
    writer.writeheader()
    writer.writerows(results)

print(f'\nDone. {len(results)} results saved to {path}')