"""Download instruct model weights from Hugging Face.

Reads HF_TOKEN from environment variable or .env file for authenticated downloads.
Supports Mistral 7B and Qwen 2.5 7B.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

MODELS = {
    "mistral": "mistralai/Mistral-7B-Instruct-v0.3",
    "qwen": "Qwen/Qwen2.5-7B-Instruct",
}


def download(model_key: str = "mistral", target_dir: str = "./models", token: str | None = None) -> Path:
    from huggingface_hub import snapshot_download

    token = token or os.getenv("HF_TOKEN")
    repo_id = MODELS.get(model_key, model_key)
    out_dir = Path(target_dir) / model_key
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {repo_id} to {out_dir} ...")
    path = snapshot_download(
        repo_id=repo_id,
        local_dir=str(out_dir),
        token=token,
        ignore_patterns=["*.pt", "*.bin"] if "safetensors" in repo_id else None,
    )
    print(f"Download complete: {path}")
    return Path(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download model weights for Aegis AI")
    parser.add_argument(
        "--model",
        choices=["mistral", "qwen", "mistralai/Mistral-7B-Instruct-v0.3", "Qwen/Qwen2.5-7B-Instruct"],
        default="mistral",
        help="Model to download (default: mistral)",
    )
    parser.add_argument("--output", default="./models", help="Output directory")
    parser.add_argument("--token", default=None, help="Hugging Face API token (or set HF_TOKEN env var)")
    args = parser.parse_args()

    download(model_key=args.model, target_dir=args.output, token=args.token)
