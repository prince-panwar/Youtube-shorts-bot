import time
import subprocess
import logging
import datetime
import sys
import os
import json
import re

# Configure logging
logging.basicConfig(
    filename='scheduler.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

STATS_FILE = 'daily_stats.json'

def load_stats():
    """Loads daily stats from JSON file."""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"date": str(datetime.date.today()), "count": 0, "topics": []}

def save_stats(stats):
    """Saves daily stats to JSON file."""
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f)

def update_stats(topic):
    """Updates the daily stats with a new video."""
    stats = load_stats()
    today = str(datetime.date.today())
    
    # Check for new day
    if stats["date"] != today:
        # Log report for previous day
        logging.info(f"📊 Daily Report ({stats['date']}): {stats['count']} videos uploaded. Topics: {', '.join(stats['topics'])}")
        print(f"[{datetime.datetime.now()}] 📊 Daily Report generated for {stats['date']}")
        
        # Reset for today
        stats = {"date": today, "count": 0, "topics": []}
    
    stats["count"] += 1
    if topic:
        stats["topics"].append(topic)
    
    save_stats(stats)

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
            
            # Extract topic from output
            output = result.stdout
            topic = "Unknown"
            # Look for "Star Found: <name>" or "Trend Found (RSS): <name>"
            match = re.search(r"Star Found: (.*)", output)
            if not match:
                match = re.search(r"Trend Found \(RSS\): (.*)", output)
            
            if match:
                topic = match.group(1).strip()
            
            logging.info(f"Video created about: {topic}")
            update_stats(topic)
            
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
