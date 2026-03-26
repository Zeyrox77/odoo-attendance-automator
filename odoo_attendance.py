import requests
import datetime
import getpass
import json
import keyring
import os
from bs4 import BeautifulSoup

try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for Python < 3.9 (though 'pytz' would be required instead).
    # This script assumes a modern Python version is running.
    ZoneInfo = None

# --- Configuration ---
# CHANGE THIS to your company's Odoo instance URL
ODOO_URL = "https://your-odoo-instance.com" 
TIMEZONE = "Europe/Zurich" # Change to your local timezone if necessary
KEYRING_SERVICE_NAME = "odoo-attendance-script"
home_dir = os.path.expanduser("~")
CONFIG_FILE = os.path.join(home_dir, "odoo_config.json")


# --- Functions ---

def get_credentials():
    """
    Fetches credentials from the OS keyring or prompts the user if they don't exist.
    Returns (username, password).
    """
    username = None
    password = None

    # 1. Try to load the username from the configuration file
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                username = config.get('username')
        except json.JSONDecodeError:
            print("WARNING: Configuration file is corrupted and will be ignored.")
            username = None

    # 2. If the username was loaded, fetch the password from the keyring
    if username:
        password = keyring.get_password(KEYRING_SERVICE_NAME, username)

    # 3. If either is missing, start the setup process
    if not username or not password:
        print("--- Initial Credential Setup ---")
        print("Your credentials will be stored securely in your operating system's Credential Manager.")
        username = input("Please enter your Odoo email address: ")
        password = getpass.getpass("Please enter your Odoo password (typing will be hidden): ")

        # Save the credentials
        keyring.set_password(KEYRING_SERVICE_NAME, username, password)
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'username': username}, f)
        
        print("-> Credentials saved successfully.")

    return username, password


def get_local_timezone():
    """Determines the local timezone based on the configuration."""
    if not ZoneInfo:
        print("ERROR: The 'zoneinfo' module is required (Standard in Python 3.9+).")
        return None
    try:
        return ZoneInfo(TIMEZONE)
    except Exception as e:
        print(f"ERROR determining timezone for '{TIMEZONE}': {e}")
        return None

def get_custom_time(prompt_message):
    """
    Prompts the user for a start and end time in HH:MM format.
    Returns a dictionary {'start': time, 'end': time} or None if cancelled.
    """
    print(f"\n--- Enter times for '{prompt_message}' ---")
    while True:
        try:
            start_str = input(f"Start time (HH:MM): ")
            end_str = input(f"End time (HH:MM):   ")

            start_time = datetime.datetime.strptime(start_str, '%H:%M').time()
            end_time = datetime.datetime.strptime(end_str, '%H:%M').time()

            if end_time <= start_time:
                print("ERROR: End time must be after start time. Please try again.")
                continue

            return {'start': start_time, 'end': end_time}

        except ValueError:
            print("ERROR: Invalid time format. Please use HH:MM (e.g., 08:30).")
            # Ask if the user wants to try again
            if input("Try again? (y/n): ").lower() != 'y':
                return None


def get_time_slots_from_user():
    """
    Shows a menu for the user to select their desired entry mode.
    Returns a list of time slots.
    """
    print("\nWhich times would you like to record?")
    print("  [1] Standard full day (08:00 - 12:00 & 13:00 - 17:00)")
    print("  [2] Half day morning (08:00 - 12:00)")
    print("  [3] Half day afternoon (13:00 - 17:00)")
    print("  [4] Manual (define custom times)")

    while True:
        choice = input("Your choice (1, 2, 3, or 4): ")
        if choice == '1':
            print("-> Standard full day selected.")
            return [
                {'start': datetime.time(8, 0), 'end': datetime.time(12, 0)},
                {'start': datetime.time(13, 0), 'end': datetime.time(17, 0)}
            ]
        elif choice == '2':
            print("-> Half day morning selected.")
            return [
                {'start': datetime.time(8, 0), 'end': datetime.time(12, 0)}
            ]
        elif choice == '3':
            print("-> Half day afternoon selected.")
            return [
                {'start': datetime.time(13, 0), 'end': datetime.time(17, 0)}
            ]
        elif choice == '4':
            print("-> Manual entry selected.")
            slots = []
            while True:
                part_choice = input("Would you like to enter times for the morning (m), afternoon (a), or both (b)? ").lower()
                if part_choice in ['m', 'b']:
                    morning_slot = get_custom_time("Morning")
                    if morning_slot:
                        slots.append(morning_slot)
                    else:
                        return [] # User cancelled
                
                if part_choice in ['a', 'b']:
                    afternoon_slot = get_custom_time("Afternoon")
                    if afternoon_slot:
                        slots.append(afternoon_slot)
                    else:
                        return [] # User cancelled

                if part_choice in ['m', 'a', 'b']:
                    return slots
                else:
                    print("Invalid input. Please choose 'm', 'a', or 'b'.")
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")


def odoo_login(session, username, password):
    login_page_url = f"{ODOO_URL}/web/login"
    print("\n1. Loading login page...")
    try:
        get_response = session.get(login_page_url, timeout=15)
        get_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"ERROR loading login page: {e}")
        return False
    
    soup = BeautifulSoup(get_response.text, 'html.parser')
    csrf_token_element = soup.find('input', {'name': 'csrf_token'})
    if not csrf_token_element:
        print("ERROR: Could not find CSRF token on the login page.")
        return False
    
    csrf_token = csrf_token_element['value']
    print("2. Sending credentials...")
    login_data = {'csrf_token': csrf_token, 'login': username, 'password': password, 'redirect': ''}
    
    try:
        post_response = session.post(login_page_url, data=login_data, timeout=15)
        post_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"ERROR submitting credentials: {e}")
        return False
    
    if 'session_id' in session.cookies:
        print("   -> Login successful.")
        return True
    else:
        print("ERROR: Login failed.")
        soup = BeautifulSoup(post_response.text, 'html.parser')
        error_message = soup.find('p', {'class': 'alert-danger'})
        if error_message:
            print(f"   -> Server message: {error_message.get_text(strip=True)}")
        else:
            print("   -> Please check your credentials.")
        return False

def get_employee_id(session):
    session_info_url = f"{ODOO_URL}/web/session/get_session_info"
    search_url = f"{ODOO_URL}/web/dataset/call_kw/hr.employee/search_read"
    print("3. Fetching User ID (uid)...")
    try:
        response = session.post(session_info_url, json={}, timeout=10)
        response.raise_for_status()
        result = response.json().get('result', {})
        user_id = result.get('uid')
        if not user_id:
            print("ERROR: Could not find User ID (uid) in session info.")
            return None
        print(f"   -> User ID found: {user_id}")
    except requests.exceptions.RequestException as e:
        print(f"ERROR fetching user information: {e}")
        return None
    
    print(f"4. Searching for associated Employee ID for User {user_id}...")
    search_payload = {"jsonrpc": "2.0", "method": "call", "params": {"model": "hr.employee", "method": "search_read", "args": [], "kwargs": {"domain": [["user_id", "=", user_id]], "fields": ["id"], "limit": 1}}}
    try:
        response = session.post(search_url, json=search_payload, timeout=10)
        response.raise_for_status()
        records = response.json().get('result', [])
        if records:
            employee_id = records[0]['id']
            print(f"   -> Employee ID found: {employee_id}")
            return employee_id
        else:
            print(f"ERROR: Could not find an employee record for User ID {user_id}.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR searching for employee: {e}")
        return None

def create_attendance_record(session, employee_id, check_in_utc, check_out_utc):
    create_url = f"{ODOO_URL}/web/dataset/call_kw/hr.attendance/create"
    check_in_str = check_in_utc.strftime('%Y-%m-%d %H:%M:%S')
    check_out_str = check_out_utc.strftime('%Y-%m-%d %H:%M:%S')
    print(f"   -> Creating record from {check_in_str} to {check_out_str} (UTC)")
    create_payload = {"jsonrpc": "2.0", "method": "call", "params": {"model": "hr.attendance", "method": "create", "args": [{"employee_id": employee_id, "check_in": check_in_str, "check_out": check_out_str}], "kwargs": {}}}
    try:
        response = session.post(create_url, json=create_payload, timeout=10)
        response.raise_for_status()
        if 'result' in response.json(): 
            return True
        else:
            print(f"ERROR from Odoo Server: {response.json().get('error', {}).get('data', {}).get('message')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR creating attendance record: {e}")
        return False


def main():
    """Main function of the script."""
    print("--- Odoo Attendance Script ---")
    
    # Show menu and get desired time slots
    time_slots = get_time_slots_from_user()
    if not time_slots:
        print("\nNo time slots selected. Exiting script.")
        return

    # Get credentials (either from OS keyring or user input)
    username, password = get_credentials()
    if not username or not password:
        print("Could not obtain credentials. Aborting.")
        return

    local_tz = get_local_timezone()
    if not local_tz: 
        return
    
    with requests.Session() as session:
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        # Disable SSL certificate verification (useful for internal servers/self-signed certs)
        session.verify = False
        requests.urllib3.disable_warnings(requests.urllib3.exceptions.InsecureRequestWarning)

        if not odoo_login(session, username, password):
            print("\nAborting due to failed login.")
            return
        
        employee_id = get_employee_id(session)
        if not employee_id:
            print("\nAborting because the Employee ID could not be determined.")
            return
        
        print("\n5. Preparing attendance records for today...")
        today = datetime.date.today()
        
        all_successful = True
        for slot in time_slots:
            local_check_in = datetime.datetime.combine(today, slot['start']).astimezone(local_tz)
            local_check_out = datetime.datetime.combine(today, slot['end']).astimezone(local_tz)
            
            # Convert to UTC for the Odoo server
            utc_check_in = local_check_in.astimezone(datetime.timezone.utc)
            utc_check_out = local_check_out.astimezone(datetime.timezone.utc)
            
            if not create_attendance_record(session, employee_id, utc_check_in, utc_check_out):
                all_successful = False
                break
            else:
                print(f"   -> Record ({slot['start'].strftime('%H:%M')} - {slot['end'].strftime('%H:%M')}) successfully created.")
    
        if all_successful:
            print("\n🎉 All attendance records have been successfully logged for today!")
        else:
            print("\n❌ Errors occurred during processing.")

    input("\nPress any key to close the window...")


if __name__ == "__main__":
    main()