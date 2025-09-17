import time
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuration
LOGIN_URL = os.getenv("LOGIN_URL")
DASHBOARD_URL = os.getenv("DASHBOARD_URL")
USERNAME = os.getenv("ROULETTE_USERNAME")
PASSWORD = os.getenv("ROULETTE_PASSWORD")
REFRESH_INTERVAL = 60  # seconds (1 minute)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HISTORY_TABLE = "roulette_history"
NUMBERS_TABLE = "roulette_numbers_individual"

# Create directories for data and logs
DATA_DIR = "roulette_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# File paths
NUMBERS_JSON_FILE = os.path.join(DATA_DIR, "roulette_numbers.json")
PROCESSED_NUMBERS_FILE = os.path.join(DATA_DIR, "processed_numbers.txt")
LOG_FILE = os.path.join(DATA_DIR, "roulette_scraper.log")

def log_message(message, level="INFO"):
    """Log message with timestamp and level"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}")

def get_number_color(number):
    """Determine the color of a roulette number"""
    number = int(number)
    if number == 0:
        return "green"
    elif number in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]:
        return "red"
    else:
        return "black"

def setup_driver():
    """Setup headless Chrome driver"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def login_and_extract_numbers():
    """Login and extract the roulette numbers"""
    driver = None
    try:
        driver = setup_driver()
        
        # Login
        log_message("Logging in...")
        driver.get(LOGIN_URL)
        time.sleep(2)
        
        # Enter credentials
        driver.find_element(By.NAME, "email").send_keys(USERNAME)
        driver.find_element(By.NAME, "senha").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)
        
        # Navigate to dashboard
        log_message("Navigating to dashboard...")
        driver.get(DASHBOARD_URL)
        time.sleep(5)
        
        # Extract numbers
        log_message("Extracting numbers...")
        numbers = driver.execute_script("""
        var table = document.querySelector("table");
        if (!table) return [];
        
        var rows = table.querySelectorAll("tr");
        var numbers = [];
        
        for (var i = 0; i < rows.length; i++) {
            var cells = rows[i].querySelectorAll("td");
            if (cells.length > 0) {
                var text = cells[0].textContent.trim();
                if (text && !isNaN(text)) {
                    numbers.push(text);
                }
            }
        }
        
        return numbers.reverse();  // Newest first
        """)
        
        if numbers and len(numbers) > 0:
            log_message(f"Extracted {len(numbers)} numbers. Most recent: {numbers[0]}")
            return numbers
        else:
            log_message("No numbers found.")
            return []
            
    except Exception as e:
        log_message(f"Error: {e}")
        return []
    finally:
        if driver:
            driver.quit()

def save_numbers_to_json(numbers):
    """Save numbers to JSON file"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "numbers": numbers
    }
    
    with open(NUMBERS_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    log_message(f"Saved {len(numbers)} numbers to {NUMBERS_JSON_FILE}")

def get_processed_numbers():
    """Get set of previously processed numbers"""
    processed = set()
    if os.path.exists(PROCESSED_NUMBERS_FILE):
        with open(PROCESSED_NUMBERS_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    processed.add(line.strip())
        log_message(f"Loaded {len(processed)} previously processed numbers")
    return processed

def add_processed_number(number):
    """Add a number to the processed numbers file"""
    with open(PROCESSED_NUMBERS_FILE, 'a') as f:
        f.write(f"{number}\n")

def create_history_entry():
    """Create an entry in the roulette_history table and return its ID"""
    log_message("Creating new entry in roulette_history table...")
    
    # Headers for Supabase API
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"  # To get the created ID back
    }
    
    # Data for the history entry (empty, just need an ID)
    data = {}
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/{HISTORY_TABLE}",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code in (200, 201, 204):
            try:
                result = response.json()
                history_id = result[0]["id"] if isinstance(result, list) and len(result) > 0 else result.get("id")
                
                if history_id:
                    log_message(f"Created history entry with ID: {history_id}")
                    return history_id
                else:
                    log_message(f"Created history entry but could not get ID. Response: {response.text}")
                    return None
            except Exception as e:
                log_message(f"Error parsing history ID from response: {e}")
                log_message(f"Response was: {response.text}")
                return None
        else:
            log_message(f"Failed to create history entry. Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        log_message(f"Error creating history entry: {e}")
        return None

def send_numbers_to_supabase(numbers):
    """Send numbers to Supabase with proper foreign key handling"""
    if not numbers:
        log_message("No numbers to send")
        return 0
    
    # First, create an entry in the history table
    history_id = create_history_entry()
    if not history_id:
        log_message("Failed to create history entry. Cannot proceed with inserting numbers.")
        return 0
    
    # Headers for Supabase API
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    success_count = 0
    
    # Insert each number with the same history ID
    for number in numbers:
        number_int = int(number)
        color = get_number_color(number)
        
        # Prepare data according to the table structure
        data = {
            # 'id' is auto-generated
            "history_entry_id": history_id,
            "number_value": number_int,
            "color": color
            # 'created_at' will be set by Supabase
        }
        
        log_message(f"Sending number {number} (color: {color}, history_entry_id: {history_id}) to Supabase...")
        
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/{NUMBERS_TABLE}",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code in (200, 201, 204):
                log_message(f"Successfully sent number {number} to Supabase")
                success_count += 1
            else:
                log_message(f"Failed to send number {number}. Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            log_message(f"Error sending number {number}: {e}")
        
        # Add a small delay between requests
        time.sleep(0.2)
    
    return success_count

def main():
    """Main function"""
    log_message("Starting Lightning Roulette Tracker with Foreign Key Handling")
    
    # Get already processed numbers
    processed_numbers = get_processed_numbers()
    
    # Main loop
    last_numbers = []
    
    while True:
        try:
            # Extract numbers
            numbers = login_and_extract_numbers()
            
            if not numbers:
                log_message("No numbers found this round. Will try again next time.")
                time.sleep(REFRESH_INTERVAL)
                continue
            
            # Save to JSON file
            save_numbers_to_json(numbers)
            
            # Skip the most recent number
            most_recent = numbers[0]
            log_message(f"Most recent number (SKIPPING): {most_recent}")
            
            # Get numbers to process (all except most recent)
            numbers_to_process = numbers[1:]
            
            # Check if we have new numbers compared to last run
            if numbers == last_numbers:
                log_message("No new numbers since last check. Waiting for next run...")
                time.sleep(REFRESH_INTERVAL)
                continue
                
            # Filter out already processed numbers
            new_numbers = [n for n in numbers_to_process if n not in processed_numbers]
            
            if not new_numbers:
                log_message("No new numbers to process. Waiting for next run...")
                last_numbers = numbers
                time.sleep(REFRESH_INTERVAL)
                continue
            
            log_message(f"Found {len(new_numbers)} new numbers to process")
            
            # Send to Supabase with proper foreign key handling
            success_count = send_numbers_to_supabase(new_numbers)
            
            # Mark as processed
            for number in new_numbers:
                processed_numbers.add(number)
                add_processed_number(number)
            
            log_message(f"Successfully processed {success_count}/{len(new_numbers)} numbers")
            
            # Update last seen numbers
            last_numbers = numbers
            
            # Wait for next check
            log_message(f"Waiting {REFRESH_INTERVAL} seconds for next check...")
            time.sleep(REFRESH_INTERVAL)
            
        except KeyboardInterrupt:
            log_message("Stopped by user")
            break
        except Exception as e:
            log_message(f"Error in main loop: {e}")
            log_message("Waiting 30 seconds before retrying...")
            time.sleep(30)

if __name__ == "__main__":
    main()