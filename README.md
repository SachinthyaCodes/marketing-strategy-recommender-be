# Marketing Strategy Recommender Backend

A FastAPI-based backend service for generating personalized marketing strategies using AI agents.

## Features

- **Profile Building**: Automatically extract and build detailed customer profiles
- **AI-Powered Recommendations**: Generate tailored marketing strategies using advanced language models
- **RESTful API**: Clean and intuitive API endpoints for integration
- **Validation**: Robust input validation using Pydantic schemas

## Project Structure

```
marketing-strategy-recommender-be/
├─ .env                      # Environment variables
├─ requirements.txt          # Python dependencies
├─ README.md                # Project documentation
├─ run_local.sh             # Local development script
├─ docker/
│  └─ Dockerfile            # Docker configuration
├─ app/
│  ├─ main.py               # FastAPI entrypoint
│  ├─ api/
│  │  └─ profile.py         # Profile API endpoints
│  ├─ agents/
│  │  └─ profile_builder.py # AI agent for profile building
│  ├─ tools/
│  │  └─ profile_extraction.py # Profile extraction utilities
│  ├─ utils/
│  │  ├─ llm.py            # LLM utilities
│  │  └─ validators.py      # Pydantic schemas
│  └─ tests/
│     └─ test_profile.py    # Unit tests
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure your environment variables
4. Run the application:
   ```bash
   ./run_local.sh
   ```

## API Endpoints

- `POST /api/profile/build` - Build customer profile from input data
- `GET /api/profile/{profile_id}` - Retrieve existing profile
- `POST /api/profile/{profile_id}/strategy` - Generate marketing strategy for profile

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Debug mode (default: True)

## Development

Run tests:
```bash
pytest app/tests/
```

Run with auto-reload:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker

Build and run with Docker:
```bash
docker build -f docker/Dockerfile -t marketing-strategy-recommender .
docker run -p 8000:8000 marketing-strategy-recommender
```