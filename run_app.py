import subprocess
import sys
import threading
import time
import argparse
from pathlib import Path

def run_api():
    """Run the FastAPI backend"""
    import uvicorn
    from app.main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

def run_frontend():
    """Run the Streamlit frontend"""
    import subprocess
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app/frontend.py", "--server.port", "8501"])

def main():
    parser = argparse.ArgumentParser(description="Run Smart Task Scheduler")
    parser.add_argument("--mode", choices=["api", "frontend", "both"], default="both", 
                       help="Run mode: api only, frontend only, or both")
    
    args = parser.parse_args()
    
    if args.mode == "api":
        print("Starting API server...")
        run_api()
    elif args.mode == "frontend":
        print("Starting frontend...")
        run_frontend()
    else:  # both
        print("Starting both API and frontend...")
        
        # Create the database file if it doesn't exist
        db_path = Path("smart_task_scheduler.db")
        if not db_path.exists():
            print("Creating database...")
            from app.database import Base, engine
            Base.metadata.create_all(bind=engine)
        
        # Start API in a separate thread
        api_thread = threading.Thread(target=run_api)
        api_thread.daemon = True
        api_thread.start()
        
        # Wait a moment for API to start
        time.sleep(2)
        
        # Run frontend in main thread
        run_frontend()

if __name__ == "__main__":
    main()