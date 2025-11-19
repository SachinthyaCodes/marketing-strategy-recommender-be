# Marketing Strategy Recommender Backend

A sophisticated AI-powered backend service for generating personalized marketing strategies for Sri Lankan SMEs, with support for mixed Sinhala-English input and integration with Ollama (open source LLM).

## 🎯 Features

- **Profile Builder Agent**: Converts messy business input into structured profiles
- **Mixed Language Support**: Handles Sinhala + English business descriptions
- **Open Source LLM**: Integrated with Ollama and Llama 3.1 8B model
- **Sri Lankan Context**: Optimized for local business environment
- **Intelligent Fallback**: Provides structured results even if LLM times out
- **FastAPI Backend**: High-performance API with automatic documentation
- **Comprehensive Validation**: Pydantic models ensure data quality

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+** installed
2. **Ollama** installed and running
3. **Llama 3.1 model** downloaded

### Installation

```bash
# Clone and navigate to project
cd marketing-strategy-recommender-be

# Install dependencies
pip install -r requirements.txt

# Set up environment variables in .env file
```

### Ollama Setup

```bash
# Install Ollama (if not done)
# Visit https://ollama.ai for installation instructions

# Pull the model
ollama pull llama3.1:8b-instruct-q4_0

# Keep model loaded (optional, improves response time)
ollama run llama3.1:8b-instruct-q4_0 "Hello"
```

### Running the Server

```bash
# Development server with auto-reload
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Production server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## 📡 API Endpoints

### Health Check
```
GET /health
```

### Profile Building
```
POST /api/profile/build
Content-Type: application/json

{
  "business_input": "Your business description here...",
  "user_context": {}  // optional
}
```

### Profile Analysis
```
POST /api/profile/analyze
Content-Type: application/json

{
  "business_input": "Quick business description"
}
```

### List Profiles
```
GET /api/profile/profiles
```

## 🧠 Profile Builder Agent

### Example Usage

**Input (Mixed Sinhala-English):**
```
මගේ business එක small restaurant එකක්. Kandy area එකේ ඉන්නේ. 
Family style Sri Lankan කෑම serve කරනවා. Daily customers 30-40 විතර එනවා.
```

**Output (Structured JSON):**
```json
{
  "business_identity": {
    "business_name": "Family Restaurant",
    "business_type": "Restaurant",
    "location": "Kandy"
  },
  "target_audience": {
    "demographics": "Families aged 25-50",
    "customer_count": "30-40 daily"
  },
  "products_services": "Sri Lankan cuisine, family-style dining",
  "strengths": ["Authentic cuisine", "Family-friendly atmosphere"],
  "challenges": ["High competition", "Marketing reach"]
}
```

## 📁 Project Structure

```
marketing-strategy-recommender-be/
├── app/
│   ├── main.py              # FastAPI application
│   ├── agents/
│   │   └── profile_builder.py   # Core AI agent
│   ├── api/
│   │   └── profile.py       # API endpoints
│   ├── utils/
│   │   ├── llm.py          # Ollama integration
│   │   └── validators.py    # Pydantic schemas
│   ├── tools/
│   │   └── profile_extraction.py # Data processing
│   └── tests/
│       └── test_profile.py  # Unit tests
├── docker/
│   └── Dockerfile          # Docker configuration
├── requirements.txt         # Python dependencies
├── .env                    # Environment configuration
├── .gitignore             # Git ignore rules
└── README.md
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# LLM Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_0

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS Settings
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Database (SQLite for demo)
DATABASE_URL=sqlite:///./marketing_strategy.db

# Logging
LOG_LEVEL=INFO
```

## 🔍 Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
ollama ps

# Start Ollama service
ollama serve

# Test model availability
ollama list

# Test model directly
ollama run llama3.1:8b-instruct-q4_0 "Hello"
```

### Common Issues

1. **Timeout Errors**: Model needs time to load initially
   - Solution: Pre-load model with `ollama run <model> "test"`

2. **Memory Issues**: Large model requires sufficient RAM
   - Solution: Use smaller quantized models or increase system memory

3. **Port Conflicts**: Default port 8000 might be in use
   - Solution: Use different port with `--port 8001`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

---

**Ready to build personalized marketing strategies for Sri Lankan SMEs! 🇱🇰**