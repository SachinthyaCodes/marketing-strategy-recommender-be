#!/usr/bin/env bash
set -e

pip install --upgrade pip

# Install CPU-only torch FIRST so sentence-transformers doesn't pull the CUDA version (~3 GB)
pip install torch --extra-index-url https://download.pytorch.org/whl/cpu

# Install the rest of the dependencies
pip install -r requirements.txt

# Pre-download the sentence-transformers model so startup is fast
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
