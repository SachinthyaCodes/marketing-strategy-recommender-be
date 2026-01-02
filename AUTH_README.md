# JWT Authentication System

Simple JWT authentication system for the Marketing Strategy Recommender backend.

## Features

- ✅ User registration with email and password
- ✅ Password hashing using bcrypt (via passlib)
- ✅ JWT token generation and verification
- ✅ Protected route middleware
- ✅ Supabase database integration
- ✅ Token expiration (24 hours default)

## Setup

### 1. Install Dependencies

```bash
cd marketing-strategy-recommender-be
pip install -r requirements.txt
```

### 2. Create Database Table

Run the SQL migration in your Supabase SQL Editor:

```sql
-- See migrations/001_create_users_table.sql
```

Or run it directly:

```bash
psql -h your-supabase-host -U postgres -d postgres -f migrations/001_create_users_table.sql
```

### 3. Configure Environment Variables

Add to your `.env` file:

```env
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production-min-32-chars
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

**Important:** Generate a strong JWT secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Start the Server

```bash
python run_server.py
# Or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### 1. Register User

**POST** `/api/v1/auth/register`

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "created_at": "2026-01-02T10:30:00Z"
}
```

### 2. Login

**POST** `/api/v1/auth/login`

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Get Current User

**GET** `/api/v1/auth/me`

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "created_at": "2026-01-02T10:30:00Z"
}
```

### 4. Protected Route Example

**GET** `/api/v1/auth/protected`

```bash
curl -X GET http://localhost:8000/api/v1/auth/protected \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Response:**
```json
{
  "message": "This is a protected route",
  "user_email": "user@example.com",
  "user_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

## Usage in Your Code

### Protecting Routes

```python
from fastapi import APIRouter, Depends
from app.services.auth import get_current_user
from app.models.user_models import TokenData

router = APIRouter()

@router.get("/my-protected-route")
async def protected_route(
    current_user: TokenData = Depends(get_current_user)
):
    """This route requires authentication"""
    return {
        "message": "Hello authenticated user!",
        "user_email": current_user.email,
        "user_id": current_user.user_id
    }
```

### Getting User from Database

```python
from fastapi import Depends
from app.services.user_database import UserDatabaseService, get_user_db_service
from app.services.auth import get_current_user
from app.models.user_models import TokenData, User

@router.get("/profile")
async def get_profile(
    current_user: TokenData = Depends(get_current_user),
    db_service: UserDatabaseService = Depends(get_user_db_service)
):
    """Get full user profile"""
    user = await db_service.get_user_by_email(current_user.email)
    
    return User(
        id=user.id,
        email=user.email,
        created_at=user.created_at
    )
```

## Architecture

```
┌─────────────────────┐
│   Client/Frontend   │
└──────────┬──────────┘
           │ POST /auth/register
           │ POST /auth/login
           ▼
┌─────────────────────┐
│   auth_routes.py    │ ← Login/Register endpoints
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  user_database.py   │ ← Database operations
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     Supabase        │ ← PostgreSQL database
│   (users table)     │
└─────────────────────┘

Protected Route Flow:
┌─────────────────────┐
│   Client/Frontend   │
└──────────┬──────────┘
           │ Authorization: Bearer <token>
           ▼
┌─────────────────────┐
│  get_current_user() │ ← JWT verification
│     (auth.py)       │
└──────────┬──────────┘
           │ TokenData
           ▼
┌─────────────────────┐
│  Protected Route    │ ← Your business logic
└─────────────────────┘
```

## Files Created

- `app/models/user_models.py` - Pydantic schemas for users and tokens
- `app/services/auth.py` - Password hashing and JWT utilities
- `app/services/user_database.py` - User CRUD operations
- `app/api/auth_routes.py` - Authentication endpoints
- `migrations/001_create_users_table.sql` - Database schema

## Security Notes

1. **JWT Secret**: Use a strong random secret (32+ characters)
2. **Password Requirements**: Minimum 8 characters (customize in `UserCreate`)
3. **Token Expiration**: Default 24 hours (adjust in `auth.py`)
4. **HTTPS**: Always use HTTPS in production
5. **Password Hashing**: Uses bcrypt with automatic salt generation

## Testing

```bash
# Test registration
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "Test1234"}'

# Test login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "Test1234"}'

# Save the token from login response
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Test protected route
curl -X GET http://localhost:8000/api/v1/auth/protected \
  -H "Authorization: Bearer $TOKEN"
```

## Customization

### Change Token Expiration

Edit `app/services/auth.py`:

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
```

### Add More User Fields

1. Update `app/models/user_models.py` to add fields
2. Update database migration to add columns
3. Update `user_database.py` to handle new fields

### Custom Password Requirements

Edit `app/models/user_models.py`:

```python
class UserCreate(UserBase):
    password: str = Field(
        ..., 
        min_length=12,  # Require 12 characters
        description="Password must be at least 12 characters"
    )
```

## Troubleshooting

### "Could not validate credentials"

- Check if JWT_SECRET matches in .env
- Verify token hasn't expired (24 hours default)
- Ensure Authorization header format: `Bearer <token>`

### "User with this email already exists"

- Email is already registered
- Use different email or implement forgot password flow

### Database connection errors

- Verify SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env
- Check if users table exists in Supabase
- Run the migration SQL script

## Next Steps

- [ ] Add password reset functionality
- [ ] Implement refresh tokens
- [ ] Add email verification
- [ ] Add OAuth providers (Google, GitHub)
- [ ] Add rate limiting
- [ ] Add audit logging
