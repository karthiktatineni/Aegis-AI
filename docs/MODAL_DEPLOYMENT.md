# Modal AI Deployment Guide for Aegis AI

This guide explains how to deploy Aegis AI to Modal's serverless GPU infrastructure.

## Configuration Highlights

- **HF Token:** Uses your Hugging Face access token configured via `HF_TOKEN` environment variable or Modal secrets for downloading Mistral 7B & Qwen 2.5 7B.
- **Serverless GPU (`keep_warm=0`):** The GPU spins up **only when a request comes**. Consumes 0 GPU credits while idle.
- **Auto-Sleep (`scaledown_window=600` & `timeout=600`):** Automatically shuts down after **10 minutes** of inactivity or session duration to strictly save credits.
- **Daily Quota (5 Requests/Day):** Strictly enforces a 5 requests per day limit tracked across cold starts via persistent `modal.Dict`. Resets at midnight UTC.
- **Persistent Volume:** Model weights and vector store embeddings are cached in `modal.Volume("aegis-models")` and `modal.Volume("aegis-data")` so weights are never downloaded more than once.

---

## Prerequisites

1. Install Modal CLI:
   ```bash
   pip install modal
   ```
2. Authenticate with your Modal account:
   ```bash
   modal setup
   ```
3. Set your Hugging Face Token:
   ```bash
   export HF_TOKEN="your_huggingface_token_here"
   ```

---

## Step 1: Pre-download Model to Modal Persistent Volume

Run the one-time download task to store Mistral 7B and embeddings onto your persistent Modal Volume:

```bash
modal run modal_app.py::download_models --model mistral
```

To download Qwen 2.5 7B instead:
```bash
modal run modal_app.py::download_models --model qwen
```

Once completed, the volume is committed and weights will be loaded in seconds on every cold start.

---

## Step 2: Deploy to Modal Serverless GPU

Deploy the application to get a permanent HTTPS URL:

```bash
modal deploy modal_app.py
```

Output will look like:
```text
✓ Created App aegis-ai
✓ Deployed fastapi_app => https://<your-username>--aegis-ai-fastapi-app.modal.run
```

---

## Step 3: Connect Frontend (Next.js)

Update your `apps/web/.env.local` or environment variable:

```env
NEXT_PUBLIC_API_URL=https://<your-username>--aegis-ai-fastapi-app.modal.run/api/v1
```

Now launch the web interface:
```bash
npm run dev:web
```

---

## Cold Start Behavior in the Frontend

- Because `keep_warm=0` is set to save your credits, the first request will initiate a cold start (~30-60 seconds for GPU container boot and weight initialization).
- The Aegis AI frontend automatically detects when the server is cold-starting and displays:
  **"Server is spinning up, please wait till the server is connected..."**
- Once connected, requests execute with full Nvidia A10G acceleration.
- If inactive for 10 minutes, the container automatically turns off and returns to zero-cost standby.
- If 5 requests are consumed in a single day, the server returns HTTP 429 and notifies the user with the exact reset time.
