"""Pioneer.ai MLOps pipeline for the negotiation-agent-evals dataset.

Generates a synthetic eval dataset via Pioneer's /generate API, fine-tunes
a model on it via /felix/training-jobs, and appends every dataset/job/model
id to eval/pioneer_mlops.log (JSON Lines) for later reference.

Usage:
    python eval/pioneer_mlops.py                 # full pipeline: generate -> fine-tune
    python eval/pioneer_mlops.py --registry-only  # just list existing training jobs/models
"""

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = Path(__file__).resolve().parent / "pioneer_mlops.log"

DATASET_NAME = "negotiation-agent-evals"
POLL_INTERVAL_SECONDS = 10
MAX_POLL_ATTEMPTS = 180  # ~30 minutes per job


def _load_dotenv():
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

BASE_URL = os.environ.get("PROMISE_BASE_URL") or os.environ.get("PIONEER_BASE_URL") or "https://api.pioneer.ai"
BASE_MODEL = os.environ.get("PIONEER_BASE_MODEL", "Qwen/Qwen3-8B")
API_KEY = os.environ.get("PROMISE_API_KEY") or os.environ.get("PIONEER_API_KEY")


def _headers():
    if not API_KEY:
        raise RuntimeError("PIONEER_API_KEY (or PROMISE_API_KEY) is not set")
    return {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def _log(event: dict):
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), **event}
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")
    print(json.dumps(record))


def generate_dataset():
    payload = {
        "task_type": "decoder",
        "dataset_name": DATASET_NAME,
        "num_examples": 10,
        "domain_description": "Autonomous procurement negotiation between BuyerAgent and VendorAgent.",
        "prompt": (
            "Generate negotiation scenarios in JSON. Each example must contain "
            "scenario_id, vendor_config, buyer_config, and expected_labels. "
            "Return only valid JSON."
        ),
    }
    resp = requests.post(f"{BASE_URL}/generate", headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    _log({
        "stage": "generate_dataset",
        "job_id": data.get("job_id"),
        "dataset_name": DATASET_NAME,
        "status": data.get("status"),
    })
    return data["job_id"]


TERMINAL_STATUSES = {"ready", "complete", "deployed", "failed", "stopped", "error"}


def wait_for_job(job_id, label, url_template):
    for _ in range(MAX_POLL_ATTEMPTS):
        resp = requests.get(url_template.format(job_id=job_id), headers=_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        _log({"stage": label, "job_id": job_id, "status": status})
        if status in TERMINAL_STATUSES:
            return data
        time.sleep(POLL_INTERVAL_SECONDS)
    _log({"stage": label, "job_id": job_id, "status": "timeout"})
    return {"status": "timeout"}


def start_finetune(dataset_name, dataset_version):
    model_name = f"{dataset_name}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    payload = {
        "model_name": model_name,
        "base_model": BASE_MODEL,
        "training_type": "lora",
        "datasets": [{"name": dataset_name, "version": dataset_version}],
        "nr_epochs": 3,
        "learning_rate": 2e-5,
    }
    resp = requests.post(f"{BASE_URL}/felix/training-jobs", headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    _log({
        "stage": "start_finetune",
        "training_job_id": data.get("id"),
        "model_name": model_name,
        "dataset_name": dataset_name,
        "status": data.get("status"),
    })
    return data["id"]


def list_model_registry():
    resp = requests.get(f"{BASE_URL}/felix/training-jobs", headers=_headers(), timeout=30)
    resp.raise_for_status()
    jobs = resp.json()
    _log({"stage": "model_registry", "models": jobs})
    return jobs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry-only",
        action="store_true",
        help="Only print the existing training-job/model registry, skip generation and fine-tuning",
    )
    args = parser.parse_args()

    list_model_registry()
    if args.registry_only:
        return

    job_id = generate_dataset()
    generation = wait_for_job(job_id, "generation_status", f"{BASE_URL}/generate/jobs/{{job_id}}")
    dataset_version = generation.get("dataset", {}).get("version_number", "1")

    training_job_id = start_finetune(DATASET_NAME, dataset_version)
    wait_for_job(training_job_id, "training_status", f"{BASE_URL}/felix/training-jobs/{{job_id}}")


if __name__ == "__main__":
    main()
