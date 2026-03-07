FROM python:3.11-slim

# HF Spaces requires the app to run on port 7860
ENV PORT=7860

WORKDIR /app

# System deps for building Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install CPU-only torch FIRST to avoid pulling CUDA (~3 GB)
RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu

# Install remaining deps
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the sentence-transformers model into the image
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application code
COPY . .

EXPOSE 7860

# Start uvicorn – HF Spaces health-checks hit the root or /health
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
