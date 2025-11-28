import time
import subprocess
import logging
import datetime
import sys

# Configure logging
logging.basicConfig(
    filename='scheduler.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_job():
    """Runs the shorts generator script."""
    print(f"[{datetime.datetime.now()}] 🚀 Starting new job...")
    logging.info("Starting new job")
    
    try:
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, "shorts_generator.py"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print(f"[{datetime.datetime.now()}] ✅ Job completed successfully.")
            logging.info("Job completed successfully")
            logging.info(f"Output: {result.stdout[-200:]}") # Log last 200 chars
        else:
            print(f"[{datetime.datetime.now()}] ❌ Job failed.")
            logging.error(f"Job failed with return code {result.returncode}")
            logging.error(f"Error Output: {result.stderr}")
            
    except Exception as e:
        print(f"[{datetime.datetime.now()}] ❌ Scheduler Error: {e}")
        logging.error(f"Scheduler Error: {e}")

if __name__ == "__main__":
    # Interval in seconds (4 hours = 14400 seconds)
    INTERVAL = 14400 
    
    print("🕒 YouTube Shorts Scheduler Started")
    print(f"⏱️  Interval: {INTERVAL/3600} hours")
    logging.info("Scheduler started")
    
    while True:
        run_job()
        
        print(f"[{datetime.datetime.now()}] 💤 Sleeping for {INTERVAL/3600} hours...")
        time.sleep(INTERVAL)
