# Marketing Strategy Recommender Backend

A FastAPI backend service for collecting and storing marketing strategy form data in Supabase.

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **Supabase Integration**: Cloud-hosted PostgreSQL database with real-time features
- **Data Validation**: Comprehensive Pydantic models for form data validation
- **RESTful API**: Clean REST endpoints for form submission and management
- **CORS Support**: Pre-configured for frontend integration
- **Docker Support**: Containerized deployment ready

## Project Structure

```
marketing-strategy-recommender-be/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoint definitions
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Application settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── form_models.py      # Pydantic data models
│   └── services/
│       ├── __init__.py
│       └── database.py         # Supabase database service
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose setup
└── .env.example               # Environment variables template
```

## Setup Instructions

### 1. Environment Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Fill in your Supabase credentials in `.env`:
   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   ```

### 2. Supabase Database Setup

Create a table in your Supabase database:

```sql
CREATE TABLE marketing_form_submissions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  form_data JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  status VARCHAR(50) DEFAULT 'submitted',
  user_agent TEXT,
  ip_address INET,
  submission_source VARCHAR(100)
);

-- Create indexes for better performance
CREATE INDEX idx_marketing_submissions_created_at ON marketing_form_submissions(created_at DESC);
CREATE INDEX idx_marketing_submissions_status ON marketing_form_submissions(status);
CREATE INDEX idx_marketing_submissions_form_data ON marketing_form_submissions USING GIN (form_data);
```

### 3. Local Development

#### Option A: Direct Python Setup

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Option B: Docker Setup

1. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

### 4. Verify Installation

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Root Endpoint: http://localhost:8000

## API Endpoints

### Form Submission
- `POST /api/v1/forms/submit` - Submit marketing form data
- `GET /api/v1/forms/submissions` - List all submissions (with pagination)
- `GET /api/v1/forms/submissions/{id}` - Get specific submission
- `PUT /api/v1/forms/submissions/{id}/status` - Update submission status
- `DELETE /api/v1/forms/submissions/{id}` - Delete submission
- `GET /api/v1/forms/stats` - Get submission statistics

### System Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check

## Frontend Integration

The API is pre-configured with CORS to accept requests from:
- `http://localhost:3000` (Next.js development server)
- `http://127.0.0.1:3000`

To submit form data from the frontend:

```javascript
const response = await fetch('http://localhost:8000/api/v1/forms/submit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(formData)
});

const result = await response.json();
```

## Data Models

The API expects form data in this structure:

```json
{
  "business_profile": {
    "business_name": "string",
    "business_type": "string",
    "business_size": "micro|small|medium",
    "business_stage": "startup|growing|established",
    "location": "string",
    "years_in_business": 0,
    "unique_selling_proposition": "string"
  },
  "budget_resources": {
    "monthly_marketing_budget": 0,
    "budget_currency": "LKR",
    "team_size": 0,
    "has_marketing_experience": true,
    "external_support_budget": 0
  },
  // ... other form sections
}
```

## Development

### Code Quality
- Use Black for code formatting: `black .`
- Use Flake8 for linting: `flake8 .`
- Use MyPy for type checking: `mypy .`

### Testing
```bash
pytest
```

## Deployment

The application is Docker-ready and can be deployed to any container platform:

- **Cloud Run** (Google Cloud)
- **ECS** (AWS)
- **Container Instances** (Azure)
- **Railway**, **Render**, **Fly.io**

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Yes |
| `DEBUG` | Enable debug mode | No (default: False) |
| `CORS_ORIGINS` | Allowed CORS origins | No |

## License

This project is part of the Marketing Strategy Recommender system.