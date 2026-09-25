import csv

path = 'outputs/results/results_master.csv'

with open(path, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

seen = {}
for r in rows:
    key = (r['technique'].strip().lower(), r['task'].strip().lower(), r['language'].strip().lower())
    # Keep the last occurrence (most recent)
    seen[key] = r

deduped = list(seen.values())

with open(path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(deduped)

print(f'Before: {len(rows)} rows')
print(f'After:  {len(deduped)} rows')