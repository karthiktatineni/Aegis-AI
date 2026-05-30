"""Download a local instruct model into the models directory.

Example:
    python scripts/download_model.py Qwen/Qwen2.5-7B-Instruct
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_id", help="Hugging Face model id or local path")
    parser.add_argument("--output", default="models", help="Directory for cached model snapshots")
    args = parser.parse_args()

    from huggingface_hub import snapshot_download

    target = Path(args.output)
    target.mkdir(parents=True, exist_ok=True)
    path = snapshot_download(repo_id=args.model_id, local_dir=target / args.model_id.replace("/", "__"))
    print(path)


if __name__ == "__main__":
    main()
