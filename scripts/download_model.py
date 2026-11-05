"""Download a local instruct model into the models directory with HF authentication.

Usage:
    python scripts/download_model.py mistral
    python scripts/download_model.py qwen
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

MODELS = {
    "mistral": "mistralai/Mistral-7B-Instruct-v0.3",
    "qwen": "Qwen/Qwen2.5-7B-Instruct",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Download model weights for Aegis AI")
    parser.add_argument("model_id", nargs="?", default="mistral", help="Hugging Face model id or shorthand (mistral/qwen)")
    parser.add_argument("--output", default="models", help="Directory for cached model snapshots")
    parser.add_argument("--token", default=None, help="Hugging Face API token (or set HF_TOKEN env var)")
    args = parser.parse_args()

    from huggingface_hub import snapshot_download

    repo_id = MODELS.get(args.model_id, args.model_id)
    folder_name = args.model_id if args.model_id in MODELS else args.model_id.replace("/", "__")
    target = Path(args.output) / folder_name
    target.mkdir(parents=True, exist_ok=True)

    token = args.token or os.getenv("HF_TOKEN")
    print(f"Downloading {repo_id} into {target} ...")
    path = snapshot_download(repo_id=repo_id, local_dir=str(target), token=token)
    print(f"Download complete: {path}")


if __name__ == "__main__":
    main()
