import requests
import time

import os

# ==================== CONFIGURATION ====================
# 1. Get Token from Environment Variable (Best for GitHub Actions) or fall back to string
TOKEN = os.getenv("ASU_TOKEN", "Bearer eyJhbGciOiJSUzI1NiJ9...") 

# 2. Your specific Class ID
TARGET_CLASS_ID = "28482"

# 3. Choose a UNIQUE name for your phone notifications
# Subscribe to this exact name in the ntfy app
NTFY_TOPIC = "asu_cse486_alerts_jeshad" 

# 4. How often to check (in seconds). 180 = 3 minutes.
CHECK_INTERVAL = 90 

# ASU API URL for CSE 486 Spring 2026
URL = 'https://eadvs-cscc-catalog-api.apps.asu.edu/catalog-microservices/api/v1/search/classes?&refine=Y&campusOrOnlineSelection=C&catalogNbr=486&honors=F&promod=F&searchType=all&subject=CSE&term=2261'
# =======================================================

headers = {
    'authorization': TOKEN,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
}

def send_notification(message):
    """Sends a push notification to your phone via ntfy.sh"""
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", 
                      data=message.encode('utf-8'),
                      headers={
                          "Title": "ASU Class Alert",
                          "Priority": "high",
                          "Tags": "mortar_board,rotating_light"
                      })
    except Exception as e:
        print(f"Failed to send notification: {e}")

def check_asu():
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] Checking for Class #{TARGET_CLASS_ID}...")
    
    try:
        response = requests.get(URL, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            classes = data.get('classes', [])
            
            # Search the list for your specific section
            target_found = False
            for c in classes:
                if str(c.get('classNbr')) == TARGET_CLASS_ID:
                    target_found = True
                    seats = int(c.get('seatsAvailable', 0))
                    
                    if seats > 0:
                        msg = f"FOUND IT! Class {TARGET_CLASS_ID} has {seats} seat(s) open. Enroll NOW!"
                        print(f"\n{msg}\n")
                        send_notification(msg)
                        return True # Exit loop
                    else:
                        print(f"Class {TARGET_CLASS_ID} is still full.")
                        return False # Keep checking
            
            if not target_found:
                print(f"Warning: Class {TARGET_CLASS_ID} not found in search results.")
                
        elif response.status_code == 401:
            print("!!! ERROR: TOKEN EXPIRED !!!")
            print("Please refresh ASU Class Search and copy a new Bearer token.")
            send_notification("Tracker Stopped: Token Expired.")
            exit() # Stop the script so you know to fix the token
            
        else:
            print(f"Unexpected error: {response.status_code}")
            
    except Exception as e:
        print(f"Connection error: {e}")
        
    return False

if __name__ == "__main__":
    print(f"Starting tracker for Class {TARGET_CLASS_ID}...")
    print(f"Notifications will be sent to: https://ntfy.sh/{NTFY_TOPIC}")
    print("-" * 50)

    # Check if running in GitHub Actions (or any CI environment)
    # If yes, run ONCE and exit. The cron job handles the scheduling.
    if os.getenv("GITHUB_ACTIONS") == "true":
        print("Running in GitHub Actions mode (Single Check)...")
        check_asu()
        # No loop. Exit script.
    else:
        # Local mode: Run in loop
        while True:
            if check_asu():
                # Successfully found a seat
                print("Task complete. Happy registering!")
                break
            
            # Wait before checking again
            time.sleep(CHECK_INTERVAL)