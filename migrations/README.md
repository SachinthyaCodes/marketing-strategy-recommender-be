# Database Setup Guide

## Quick Setup (Supabase)

### Option 1: Run Complete Setup (Recommended)

Copy and paste the entire content of **`000_complete_setup.sql`** into your Supabase SQL Editor and click "Run".

This will create:
- ✅ Users table (authentication)
- ✅ Marketing form submissions table (with JSONB columns)
- ✅ All indexes for performance
- ✅ Triggers for auto-updating timestamps
- ✅ Helpful comments and documentation

### Option 2: Run Individual Migrations

If you prefer step-by-step setup:

1. **Create users table:**
   ```sql
   -- Copy from: 001_create_users_table.sql
   ```

2. **Create submissions table:**
   ```sql
   -- Copy from: 002_create_submissions_table.sql
   ```

## Access Your Supabase SQL Editor

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Select your project
3. Click "SQL Editor" in the left sidebar
4. Click "New query"
5. Paste the SQL from `000_complete_setup.sql`
6. Click "Run" or press `Ctrl+Enter`

## Verify Tables Were Created

Run this query:

```sql
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name IN ('users', 'marketing_form_submissions')
ORDER BY table_name, ordinal_position;
```

Expected output:
```
table_name                    | column_name      | data_type
------------------------------|------------------|---------------------------
marketing_form_submissions    | id               | uuid
marketing_form_submissions    | user_id          | uuid
marketing_form_submissions    | form_data        | jsonb
marketing_form_submissions    | strategy_data    | jsonb
marketing_form_submissions    | status           | character varying
marketing_form_submissions    | created_at       | timestamp with time zone
marketing_form_submissions    | updated_at       | timestamp with time zone
users                         | id               | uuid
users                         | email            | character varying
users                         | hashed_password  | text
users                         | created_at       | timestamp with time zone
users                         | updated_at       | timestamp with time zone
```

## Table Schemas

### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,              -- Auto-generated UUID
    email VARCHAR(255) UNIQUE,        -- User email (unique)
    hashed_password TEXT,             -- Bcrypt hashed password
    created_at TIMESTAMPTZ,           -- Account creation time
    updated_at TIMESTAMPTZ            -- Last update time
);
```

### marketing_form_submissions
```sql
CREATE TABLE marketing_form_submissions (
    id UUID PRIMARY KEY,              -- Auto-generated UUID
    user_id UUID,                     -- Foreign key to users(id)
    form_data JSONB,                  -- Raw form data from frontend
    strategy_data JSONB,              -- AI-generated strategy
    status VARCHAR(50),               -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMPTZ,           -- Submission creation time
    updated_at TIMESTAMPTZ            -- Last update time
);
```

## Example Data Structure

### form_data (JSONB column)
```json
{
  "business_info": {
    "business_name": "Green Leaf Café",
    "industry": "food_beverage",
    "business_stage": "growth",
    "years_in_business": 3,
    "location": "Colombo"
  },
  "target_audience": {
    "age_groups": ["25-34", "35-44"],
    "interests": ["coffee", "healthy eating"]
  },
  "budget_resources": {
    "monthly_budget": "1000-2500",
    "has_marketing_team": false,
    "content_creation_capacity": ["photography", "social_media"]
  }
}
```

### strategy_data (JSONB column)
```json
{
  "marketing_pillars": [
    {
      "name": "Social Media Marketing",
      "description": "Build community through Instagram and Facebook",
      "tactics": [
        "Daily Instagram Stories",
        "Weekly Reels showcasing menu items",
        "User-generated content campaigns"
      ]
    }
  ],
  "platform_strategies": {
    "instagram": {
      "focus_areas": ["visual content", "stories", "reels"],
      "budget_percentage": 40
    },
    "facebook": {
      "focus_areas": ["community building", "events"],
      "budget_percentage": 30
    }
  },
  "budget_allocation": {
    "content_creation": 40,
    "paid_advertising": 35,
    "tools_software": 15,
    "influencer_partnerships": 10
  }
}
```

## Common Issues & Solutions

### Issue: "relation 'users' does not exist"
**Solution:** You haven't run the SQL migrations yet. Run `000_complete_setup.sql` in Supabase SQL Editor.

### Issue: "permission denied for table users"
**Solution:** Your Supabase service role key needs permissions. Check your `.env` file has `SUPABASE_SERVICE_ROLE_KEY` (not anon key).

### Issue: "duplicate key value violates unique constraint 'users_email_key'"
**Solution:** User with that email already exists. This is expected behavior.

### Issue: Foreign key constraint violation
**Solution:** Make sure you're creating submissions with a valid `user_id` that exists in the `users` table.

## Querying JSONB Data

### Find submissions by business name:
```sql
SELECT id, form_data->>'business_info'->>'business_name' as business_name
FROM marketing_form_submissions
WHERE form_data->'business_info'->>'business_name' = 'Green Leaf Café';
```

### Find completed strategies:
```sql
SELECT id, user_id, strategy_data
FROM marketing_form_submissions
WHERE status = 'completed'
  AND strategy_data IS NOT NULL;
```

### Get all submissions for a user:
```sql
SELECT s.id, s.status, s.created_at, u.email
FROM marketing_form_submissions s
JOIN users u ON s.user_id = u.id
WHERE u.email = 'user@example.com'
ORDER BY s.created_at DESC;
```

## Indexes for Performance

The following indexes are automatically created:

- `idx_users_email` - Fast email lookups for login
- `idx_submissions_user_id` - Fast user submission queries
- `idx_submissions_status` - Filter by status efficiently
- `idx_submissions_created_at` - Sort by creation date
- `idx_submissions_form_data_gin` - Fast JSON queries on form_data
- `idx_submissions_strategy_data_gin` - Fast JSON queries on strategy_data

## Testing the Setup

After running migrations, test with your backend:

```bash
# Terminal 1: Start backend
cd marketing-strategy-recommender-be
python run_server.py

# Terminal 2: Test authentication
python test_auth_api.py

# Should create user in database and show:
# ✅ User Registration - PASSED
# ✅ User Login - PASSED
```

## Backup & Restore

### Backup (from Supabase Dashboard):
1. Go to Database → Backups
2. Click "Create backup"
3. Download SQL dump if needed

### Restore:
```bash
# If using local PostgreSQL
psql -U postgres -d your_database < backup.sql
```

## Next Steps

1. ✅ Run `000_complete_setup.sql` in Supabase
2. ✅ Verify tables exist with verification query
3. ✅ Update `.env` file with Supabase credentials
4. ✅ Test backend: `python test_auth.py`
5. ✅ Test API: `python test_auth_api.py` (with backend running)
6. ✅ Test frontend: Visit `http://localhost:3000` and register/login
