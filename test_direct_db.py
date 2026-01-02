import sys
sys.path.insert(0, r'D:\Projects\Marketing-Strategy-Recommnder\marketing-strategy-recommender-be')

import asyncio
from app.services.user_database import UserDatabaseService
from app.models.user_models import UserCreate

async def test_create_user():
    try:
        print("Initializing UserDatabaseService...")
        db_service = UserDatabaseService()
        print("✅ Service initialized successfully!")
        
        print("\nCreating test user...")
        user = UserCreate(email="directtest@example.com", password="password123")
        result = await db_service.create_user(user)
        print(f"✅ User created: {result.email}, ID: {result.id}")
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_create_user())
