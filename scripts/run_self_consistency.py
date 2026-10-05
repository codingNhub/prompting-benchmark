# One-off driver for the self-consistency rerun. Uses the repo's predict_example()
# and the runner's row format, but retries an example after an API/network error
# instead of recording it as a model failure; run_experiment() then finalises metrics.
import csv, os, sys, time
sys.path.insert(0, os.getcwd())
from src.experiment_runner import predict_example, run_experiment
from src.config_manager import load_config
from src.dataset_loader import load_dataset
from src.prompt_manager import load_template

config = load_config()
seed = config["experiment"]["random_seed"]
template = load_template("self_consistency")
FIELDS = ["id", "text", "reference", "prediction", "status", "failure_reason",
          "raw_response", "input_tokens", "output_tokens"]

for task in sys.argv[1:]:
    path = f"outputs/predictions/self_consistency_{task}_english.csv"
    examples = load_dataset(task, "english")
    done = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            done = {int(r["id"]) for r in csv.DictReader(f)}
    for n, ex in enumerate(examples):
        if ex["id"] in done:
            continue
        for attempt in range(1, 21):
            try:
                out = predict_example("self_consistency", task, ex, examples, config, template, seed)
                break
            except Exception as e:
                msg = str(e)
                if "per day" in msg.lower() or "401" in msg:
                    print(f"STOPPED {task} id={ex['id']} (daily token limit or auth error; "
                          f"rerun the same command to resume): {msg[:200]}", flush=True)
                    sys.exit(2)
                print(f"API_ERROR {task} id={ex['id']} attempt={attempt}: {msg[:120]}", flush=True)
                time.sleep(300)
        else:
            print(f"GAVE_UP {task} id={ex['id']}", flush=True)
            sys.exit(1)
        row = {"id": ex["id"], "text": ex["text"][:100], "reference": ex["label"],
               "prediction": str(out["prediction"]), **{k: out[k] for k in FIELDS[4:]}}
        new_file = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if new_file:
                w.writeheader()
            w.writerow(row)
        if (n + 1) % 10 == 0 or out["status"] != "ok":
            print(f"PROGRESS {task} {n + 1}/100 last_status={out['status']}", flush=True)
    result = run_experiment("self_consistency", task)
    print(f"DONE {task} " + " ".join(f"{k}={result.get(k)}" for k in
          ("macro_f1", "accuracy", "entity_f1", "flagged_count")), flush=True)
