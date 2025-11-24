"""
Simple startup script for the FastAPI application
This ensures we run from the correct directory with proper Python path
"""
import os
import sys
from pathlib import Path

# Get the directory containing this script (should be the backend root)
BACKEND_DIR = Path(__file__).parent.absolute()

# Add the backend directory to Python path
sys.path.insert(0, str(BACKEND_DIR))

# Change working directory to backend directory
os.chdir(BACKEND_DIR)

# Now we can import and run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(BACKEND_DIR)]
    )