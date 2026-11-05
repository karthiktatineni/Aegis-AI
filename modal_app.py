"""Modal AI deployment for Aegis AI.

Key Features:
1. One-time pre-download function using HF token (via HF_TOKEN env var / Modal secret)
   cached to persistent modal.Volume ("aegis-models").
2. Serverless GPU: Cold-start on demand (keep_warm=0), consumes 0 credits when idle.
3. Strict 5 requests per day limit tracked across cold starts via modal.Dict ("aegis-quota").
4. Sleeps after 10 minutes (scaledown_window=600, timeout=600) even during active sessions
   to guarantee credits are never wasted.
5. Serves full FastAPI backend (streaming SSE, RAG, memory, tools, agents).

Usage:
    # 1. First-time: Download model weights to Modal Volume
    modal run modal_app.py::download_models --model mistral

    # 2. Deploy serverless GPU app
    modal deploy modal_app.py

    # 3. Test locally in ephemeral container
    modal serve modal_app.py
"""

from __future__ import annotations

import os
from pathlib import Path

import modal

# ---------------------------------------------------------------------------
# Modal App & Persistent Storage
# ---------------------------------------------------------------------------
APP_NAME = "aegis-ai"
app = modal.App(APP_NAME)

# Persistent volume for weights (download once, never re-download)
model_volume = modal.Volume.from_name("aegis-models", create_if_missing=True)
data_volume = modal.Volume.from_name("aegis-data", create_if_missing=True)

# Persistent dictionary for tracking the 5 requests/day credit-guard across containers
daily_quota_dict = modal.Dict.from_name("aegis-daily-quota", create_if_missing=True)

def _get_hf_token() -> str:
    token = os.getenv("HF_TOKEN", "")
    if not token:
        env_file = Path(".env")
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("HF_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                    break
    return token


HF_TOKEN = _get_hf_token()
DAILY_REQUEST_LIMIT = 5

MODELS = {
    "mistral": "mistralai/Mistral-7B-Instruct-v0.3",
    "qwen": "Qwen/Qwen2.5-7B-Instruct",
    "embeddings": "sentence-transformers/all-MiniLM-L6-v2",
}

# ---------------------------------------------------------------------------
# Container Image Definition
# ---------------------------------------------------------------------------
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "curl")
    .pip_install(
        "torch>=2.4.0",
        "transformers>=4.44.0",
        "accelerate>=0.34.0",
        "bitsandbytes>=0.43.0",
        "sentence-transformers>=3.0.1",
        "huggingface-hub>=0.24.6",
        "fastapi>=0.115.0",
        "uvicorn>=0.30.6",
        "pydantic>=2.8.2",
        "pydantic-settings>=2.4.0",
        "sqlalchemy>=2.0.32",
        "aiosqlite>=0.20.0",
        "chromadb>=0.5.5",
        "pypdf>=4.3.1",
        "python-docx>=1.1.2",
        "python-multipart>=0.0.9",
        "rank-bm25>=0.2.2",
        "greenlet>=3.0.3",
        "httpx>=0.27.2",
    )
    # Add local application code into container image
    .add_local_dir("apps/api/app", remote_path="/root/app")
)


# ---------------------------------------------------------------------------
# 1. Download Model Function (Pre-download step)
# ---------------------------------------------------------------------------
@app.function(
    image=image,
    volumes={"/models": model_volume},
    timeout=3600,  # 1 hour allowed for initial one-time download
)
def download_models(model: str = "mistral", token: str | None = None):
    """Download models into Modal Volume. Run once with:

    modal run modal_app.py::download_models --model mistral
    """
    from huggingface_hub import snapshot_download

    token = token or _get_hf_token()
    repo_id = MODELS.get(model, model)
    target_dir = Path("/models") / model
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"============================================================")
    print(f"Downloading {repo_id} to /models/{model} on Modal Volume")
    print(f"============================================================")

    snapshot_download(
        repo_id=repo_id,
        local_dir=str(target_dir),
        token=token or None,
    )
    print(f"Model {repo_id} downloaded successfully.")

    # Also pre-download sentence transformers embedding model for fast RAG
    embed_repo = MODELS["embeddings"]
    embed_target = Path("/models/embeddings")
    embed_target.mkdir(parents=True, exist_ok=True)
    print(f"Downloading embedding model {embed_repo} ...")
    snapshot_download(repo_id=embed_repo, local_dir=str(embed_target), token=token or None)
    print("Embedding model downloaded.")

    # Commit persistent volume
    model_volume.commit()
    print("Volume committed. Future GPU containers will load weights immediately!")
    return f"Success: {model} and embeddings cached in volume"


# ---------------------------------------------------------------------------
# Quota Helper Functions (Only 5 requests per day)
# ---------------------------------------------------------------------------
def _today_utc() -> str:
    from datetime import timezone, datetime
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def check_daily_quota() -> tuple[bool, int, int]:
    """Returns (is_allowed, used_today, remaining)."""
    today = _today_utc()
    try:
        used = int(daily_quota_dict.get(today, 0))
    except Exception:
        used = 0
    remaining = max(0, DAILY_REQUEST_LIMIT - used)
    return remaining > 0, used, remaining


def increment_daily_quota() -> int:
    """Consumes 1 request from today's budget."""
    today = _today_utc()
    try:
        used = int(daily_quota_dict.get(today, 0))
    except Exception:
        used = 0
    new_count = used + 1
    daily_quota_dict[today] = new_count
    return new_count


# ---------------------------------------------------------------------------
# 2. Serverless GPU ASGI App
# ---------------------------------------------------------------------------
@app.function(
    image=image,
    gpu="A10G",  # Fast Nvidia A10G 24GB GPU
    volumes={"/models": model_volume, "/data": data_volume},
    # COLD START ONLY WHEN REQUEST COMES:
    min_containers=0,  # 0 containers running when idle = 0 credits wasted
    # SLEEP AFTER 10 MINUTES IDLE:
    scaledown_window=600,  # 600 seconds = 10 minutes idle timeout
    # SESSION DURATION LIMIT:
    timeout=600,  # 10 minutes hard timeout to save credits even while active
    max_containers=1,  # Strictly serialize to prevent concurrency credit burn
)
@modal.asgi_app()
def fastapi_app():
    """Serves Aegis AI on Modal GPU."""
    import sys
    sys.path.insert(0, "/root")

    import os
    os.environ["AEGIS_ENV"] = "production"
    os.environ["LLM_PROVIDER"] = "transformers" if Path("/models/mistral").exists() or Path("/models/qwen").exists() else "mock"
    os.environ["LOCAL_MODEL_ID"] = "/models/mistral" if Path("/models/mistral").exists() else "mistralai/Mistral-7B-Instruct-v0.3"
    os.environ["LOCAL_EMBEDDING_MODEL"] = "/models/embeddings" if Path("/models/embeddings").exists() else "sentence-transformers/all-MiniLM-L6-v2"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:////data/aegis.db"
    os.environ["CHROMA_PATH"] = "/data/chroma"
    os.environ["UPLOAD_DIR"] = "/data/uploads"
    os.environ["WORKSPACE_ROOT"] = "/data/workspace"

    from fastapi import FastAPI, HTTPException, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
    from app.main import app as aegis_fastapi

    # Allow all CORS origins for deployed web frontend
    aegis_fastapi.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware to enforce the 5 requests/day limit on expensive inference endpoints
    @aegis_fastapi.middleware("http")
    async def quota_middleware(request: Request, call_next):
        # Apply 5 requests/day quota strictly on chat stream and message generation
        if request.url.path.endswith("/stream") or request.url.path.endswith("/messages") or request.url.path.endswith("/agents/run"):
            allowed, used, remaining = check_daily_quota()
            if not allowed:
                return Response(
                    content=(
                        f'{{"detail": "Daily GPU limit reached: Aegis AI is capped at {DAILY_REQUEST_LIMIT} requests '
                        f'per day to conserve Modal credits ({used}/{DAILY_REQUEST_LIMIT} used today). '
                        f'Resets at midnight UTC.", "daily_limit": {DAILY_REQUEST_LIMIT}, "used_today": {used}}}'
                    ),
                    status_code=429,
                    media_type="application/json",
                )
            increment_daily_quota()

        response = await call_next(request)
        return response

    # Quota endpoint
    @aegis_fastapi.get("/api/v1/modal-status")
    def modal_status():
        allowed, used, remaining = check_daily_quota()
        return {
            "status": "online",
            "gpu": "A10G",
            "idle_sleep_minutes": 10,
            "daily_limit": DAILY_REQUEST_LIMIT,
            "requests_used_today": used,
            "requests_remaining_today": remaining,
            "models_available": {
                "mistral": Path("/models/mistral").exists(),
                "qwen": Path("/models/qwen").exists(),
                "embeddings": Path("/models/embeddings").exists(),
            },
        }

    return aegis_fastapi
