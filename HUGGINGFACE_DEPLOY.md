# Hugging Face Spaces Deployment Guide (Backend)

## Overview

This guide deploys the **FastAPI backend** to **Hugging Face Spaces (free tier)** using a Docker-based Space. HF Spaces free tier gives you **2 vCPU, 16 GB RAM, 50 GB disk**.

Your backend URL will be:
```
https://<your-hf-username>-<space-name>.hf.space
```

---

## Step 1 — Create a Hugging Face Space

1. Go to [https://huggingface.co/new-space](https://huggingface.co/new-space)
2. Fill in:
   - **Space name**: `marketing-backend` (or any name you like)
   - **License**: MIT (or your preference)
   - **SDK**: Select **Docker**
   - **Hardware**: **CPU basic (Free)**
   - **Visibility**: **Public** (free tier requires public)
3. Click **Create Space**

> **Important**: Free tier Spaces must be **public**. Your code will be visible, but secrets (API keys) are stored securely and never exposed.

---

## Step 2 — Add Secrets (Environment Variables)

Your app requires 3 environment variables. **Never commit these to code.**

1. Go to your Space → **Settings** → **Repository secrets**
2. Add these secrets:

| Secret Name     | Value                        |
|-----------------|------------------------------|
| `SUPABASE_URL`  | Your Supabase project URL    |
| `SUPABASE_KEY`  | Your Supabase anon/service key |
| `GROQ_API_KEY`  | Your Groq API key            |

These are injected as environment variables at runtime, which `pydantic-settings` will pick up automatically.

---

## Step 3 — Push Your Backend Code to the Space

### Option A: Clone the Space and copy files

```bash
# Clone the empty HF Space repo
git clone https://huggingface.co/spaces/<your-username>/marketing-backend
cd marketing-backend

# Copy your backend files into the cloned repo
# Copy these files/folders from your backend directory:
#   - Dockerfile
#   - requirements.txt
#   - app/           (entire folder)
#   - build.sh       (optional, not needed with Docker)
```

### Option B: Use HF CLI

```bash
pip install huggingface_hub
huggingface-cli login   # paste your HF token

# Then push from your backend folder
cd backend
git init
git remote add space https://huggingface.co/spaces/<your-username>/marketing-backend
git add Dockerfile requirements.txt app/
git commit -m "Initial deployment"
git push space main
```

### Required files in the Space repo:

```
marketing-backend/
├── Dockerfile            ← Created for you
├── requirements.txt      ← Already exists
└── app/
    ├── __init__.py
    ├── main.py
    ├── ai_core/
    ├── api/
    ├── config/
    ├── database/
    ├── models/
    └── services/
```

> **Do NOT push** `.env`, `.git/`, `__pycache__/`, `migrations/`, `test_*.py`, or `postman_collection.json`.

---

## Step 4 — Verify Deployment

Once you push, HF Spaces will automatically build your Docker image and start the container. You can watch the build logs in the Space UI.

1. Go to your Space page — you'll see build logs
2. Wait for the build to complete (first build takes ~5-10 minutes due to torch + sentence-transformers download)
3. Test the health endpoint:
   ```
   https://<your-username>-marketing-backend.hf.space/health
   ```
4. Test the API docs:
   ```
   https://<your-username>-marketing-backend.hf.space/docs
   ```

---

## Step 5 — Update Your Vercel Frontend

Update your frontend `.env` (or Vercel environment variables) to point to the new backend:

```env
NEXT_PUBLIC_STRATEGY_BASE_URL=https://<your-username>-marketing-backend.hf.space
```

Also update this in **Vercel Dashboard** → Your Project → **Settings** → **Environment Variables**.

---

## Troubleshooting

### Build fails with "out of memory"
The free tier has enough RAM for CPU-only torch. If the build still fails:
- Make sure you're using the `--extra-index-url https://download.pytorch.org/whl/cpu` for torch (already configured in the Dockerfile)
- The sentence-transformers model download happens at build time, not runtime

### Space says "Building" for a long time
- First build can take 5-10 minutes. Check the **Logs** tab.

### "Application Error" after build succeeds
- Check **Logs** tab for Python errors
- Most likely cause: missing secrets. Go to **Settings → Repository secrets** and verify all 3 are set.

### Space goes to sleep (cold start)
- Free tier Spaces **sleep after ~48 hours of inactivity**
- First request after sleep takes ~30-60 seconds (cold start)
- The app will auto-wake on any incoming request
- To keep it alive, you can set up a free cron ping (e.g., UptimeRobot or cron-job.org hitting `/health` every 30 min)

### CORS errors from Vercel frontend
- The backend already allows all origins (`allow_origins=["*"]`), so CORS should work out of the box.

### API keys not working
- HF Spaces injects secrets as environment variables — no `.env` file is needed
- Double-check secret names match exactly: `SUPABASE_URL`, `SUPABASE_KEY`, `GROQ_API_KEY`

---

## Keeping the Space Awake (Optional)

Free Spaces sleep after inactivity. To prevent this:

1. Go to [https://cron-job.org](https://cron-job.org) (free)
2. Create a cron job that hits:
   ```
   https://<your-username>-marketing-backend.hf.space/health
   ```
3. Set interval: **every 25 minutes**

This keeps the Space alive and responsive.

---

## Updating Your Backend

To deploy updates, simply push new commits to the Space repo:

```bash
cd marketing-backend
git add .
git commit -m "Update backend"
git push space main
```

HF Spaces will automatically rebuild and redeploy.
