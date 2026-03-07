#!/usr/bin/env bash
set -e

pip install --upgrade pip
pip install -r requirements.txt

# Pre-download the sentence-transformers model so startup is fast
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
