#!/bin/bash

# Marketing Strategy Recommender - Local Development Runner

echo "Starting Marketing Strategy Recommender Backend..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "Environment variables loaded from .env"
else
    echo "Warning: .env file not found. Using default values."
fi

# Set default values if not provided
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8000}

echo "Starting server on ${HOST}:${PORT}"

# Run the FastAPI application with uvicorn
uvicorn app.main:app --reload --host $HOST --port $PORT