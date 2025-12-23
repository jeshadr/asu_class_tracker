import requests
import time
import sys
import os

# ==================== CONFIGURATION ====================
# DISCOVERY: The ASU API accepts "Bearer null" without real authentication!
# This means no token refresh is needed - it works indefinitely!
TOKEN = "Bearer null"

# Your specific Class ID
TARGET_CLASS_ID = "28482"

# Choose a UNIQUE name for your phone notifications
# Subscribe to this exact name in the ntfy app
NTFY_TOPIC = "asu_cse486_alerts_jeshad"

# Discord Webhook URL (optional - leave empty to disable)
# Get this from: Discord Server → Channel Settings → Integrations → Webhooks
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1452840080732323903/M6hdXbMZRDhkZlOJsUzJVrUnQ76FEGJ7BZ33X2p0yeOeB7HG39tA0g6aLAkIJwitZZ-t"  # Paste your webhook URL here

# How often to check (in seconds). 90 = 1.5 minutes.
CHECK_INTERVAL = 90

# ASU API URL for CSE 486 Spring 2026
URL = 'https://eadvs-cscc-catalog-api.apps.asu.edu/catalog-microservices/api/v1/search/classes?&refine=Y&campusOrOnlineSelection=C&catalogNbr=486&honors=F&promod=F&searchType=all&subject=CSE&term=2261'
# =======================================================

headers = {
    'authorization': TOKEN,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
}

def send_notification(message):
    """Sends notifications via ntfy (phone) and Discord"""
    
    # Send to ntfy (phone notification)
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", 
                      data=message.encode('utf-8'),
                      headers={
                          "Title": "ASU Class Alert",
                          "Priority": "high",
                          "Tags": "mortar_board,rotating_light"
                      })
        print(f"📱 Phone notification sent!")
    except Exception as e:
        print(f"Failed to send phone notification: {e}")
    
    # Send to Discord (if webhook is configured)
    if DISCORD_WEBHOOK:
        try:
            discord_message = {
                "content": f"🚨 **ASU CLASS ALERT** 🚨\n\n{message}\n\n🔗 [Enroll Now](https://webapp4.asu.edu/catalog/)",
                "username": "ASU Class Tracker",
            }
            requests.post(DISCORD_WEBHOOK, json=discord_message)
            print(f"💬 Discord notification sent!")
        except Exception as e:
            print(f"Failed to send Discord notification: {e}")

def check_asu():
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] Checking for Class #{TARGET_CLASS_ID}...")
    
    try:
        response = requests.get(URL, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            classes = data.get('classes', [])
            
            # Search the list for your specific section
            for c in classes:
                # Parse Class Number from nested CLAS object
                clas_info = c.get('CLAS', {})
                class_nbr = str(clas_info.get('CLASSNBR', 'Unknown'))
                
                if class_nbr == TARGET_CLASS_ID:
                    # Parse Seat Info
                    seat_info = c.get('seatInfo', {})
                    enrl_cap = int(seat_info.get('ENRL_CAP') or 0)
                    enrl_tot = int(seat_info.get('ENRL_TOT') or 0)
                    seats = enrl_cap - enrl_tot
                    
                    if seats > 0:
                        msg = f"🎉 FOUND IT! Class {TARGET_CLASS_ID} has {seats} seat(s) open. Enroll NOW!"
                        print(f"\n{msg}\n")
                        send_notification(msg)
                        return True  # Seat found!
                    else:
                        print(f"Class {TARGET_CLASS_ID} is still full. ({enrl_tot}/{enrl_cap} enrolled)")
                        return False  # Keep checking
            
            # Class not found in results
            print(f"Warning: Class {TARGET_CLASS_ID} not found in search results.")
            return False
                
        else:
            print(f"API Error: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Connection error: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print(f"ASU CLASS TRACKER - Monitoring Class #{TARGET_CLASS_ID}")
    print(f"Notifications: https://ntfy.sh/{NTFY_TOPIC}")
    print(f"Using 'Bearer null' (no token refresh needed!)")
    print("="*50)

    # Check if running in GitHub Actions OR if --once flag is used
    is_github = os.getenv("GITHUB_ACTIONS") == "true"
    is_single_run = "--once" in sys.argv

    if is_github or is_single_run:
        print("Running single check...")
        check_asu()
    else:
        # Local mode: Run in loop
        print(f"Checking every {CHECK_INTERVAL} seconds. Press Ctrl+C to stop.")
        print("-"*50)
        
        while True:
            if check_asu():
                print("\n🎉 Task complete! Happy registering!")
                break
            
            time.sleep(CHECK_INTERVAL)