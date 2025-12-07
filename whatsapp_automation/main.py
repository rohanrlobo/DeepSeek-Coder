import pandas as pd
import tkinter as tk
from tkinter import filedialog
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
import urllib.parse
import ctypes
import platform
import os
import requests
import csv

# Constants
LOG_FILE = "message_log.csv"
WHATSAPP_WEB_URL = "https://web.whatsapp.com"
CONNECTIVITY_CHECK_URL = "https://www.google.com"

# Prevent Sleep Class
class PreventSleep:
    def __enter__(self):
        if platform.system() == "Windows":
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)
        elif platform.system() == "Darwin":
            self.proc = os.popen("caffeinate -dims")
        elif platform.system() == "Linux":
            os.system("xset s off -dpms")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if platform.system() == "Windows":
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        elif platform.system() == "Darwin":
            if hasattr(self, 'proc'):
                self.proc.close()
        elif platform.system() == "Linux":
            os.system("xset s on +dpms")

def is_internet_available():
    """Checks for internet connectivity."""
    try:
        requests.get(CONNECTIVITY_CHECK_URL, timeout=5)
        return True
    except requests.RequestException:
        return False

def get_excel_file():
    """Opens a file dialog to select an Excel file."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(
        title="Select the Excel file with contacts",
        filetypes=[("Excel Files", "*.xlsx *.xls")]
    )
    return file_path

def read_contacts(file_path):
    """Reads contacts from the specified Excel file."""
    if not file_path:
        print("No file selected. Exiting.")
        return None
    try:
        df = pd.read_excel(file_path)
        print("Successfully loaded contacts:")
        print(df)
        return df
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while reading the Excel file: {e}")
        return None

def initialize_driver():
    """Initializes the Chrome WebDriver using webdriver-manager and user profile persistence."""
    try:
        print("Setting up ChromeDriver...")
        options = webdriver.ChromeOptions()
        options.add_argument("--user-data-dir=chrome-data")
        options.add_argument("--profile-directory=Default")
        # Ensure the browser stays open if script ends (optional, but good for debugging)
        options.add_experimental_option("detach", True)

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(WHATSAPP_WEB_URL)
        print("Please scan the QR code in WhatsApp Web...")

        # Wait for WhatsApp Web to load (looking for the side panel/chat list)
        # Using the selector from the provided working code: //div[@contenteditable="true"]
        # This usually corresponds to the search box or message input, indicating login is successful.
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"]'))
            )
            print("WhatsApp Web loaded successfully!")
            return driver
        except TimeoutException:
            print("Timeout: Failed to load WhatsApp Web. Please try again.")
            driver.quit()
            return None

    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        print("Please make sure you have Google Chrome installed.")
        return None

def format_phone_number(phone_number):
    """Formats the phone number."""
    phone_str = str(phone_number).strip()

    # Remove .0 if it exists (common float artifact from Excel)
    if phone_str.endswith('.0'):
        phone_str = phone_str[:-2]

    # Check if it is exactly 10 digits (assuming numeric only)
    if phone_str.isdigit() and len(phone_str) == 10:
        return f"+91{phone_str}"

    if not phone_str.startswith('+'):
        return '+' + phone_str

    return phone_str

def log_status(phone_number, message, status, failure_reason=""):
    """Appends log entries to a CSV file immediately."""
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="", encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["PhoneNumber", "Message", "Status", "FailureReason"])
        writer.writerow([phone_number, message, status, failure_reason])

def send_whatsapp_message(driver, phone_number, message):
    """Sends a WhatsApp message using the URL method."""
    try:
        # Check internet before proceeding
        while not is_internet_available():
            print("No internet connection. Retrying in 10 seconds...")
            time.sleep(10)

        # Format the phone number
        phone_number = format_phone_number(phone_number)
        encoded_message = urllib.parse.quote(message)

        # Create the URL to open a chat with the message pre-filled
        url = f"https://web.whatsapp.com/send?phone={phone_number}&text={encoded_message}"
        driver.get(url)

        try:
            # Wait for the send button to appear
            # Using selector from provided working code: //span[@data-icon="send"]
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//span[@data-icon="send"]'))
            )
            send_button = driver.find_element(By.XPATH, '//span[@data-icon="send"]')
            send_button.click()

            time.sleep(random.uniform(2, 4)) # Short delay after clicking send
            return True, "Success"
        except TimeoutException:
            failure_reason = "Chat not loaded or number not on WhatsApp"
            return False, failure_reason

    except Exception as e:
        failure_reason = str(e)
        return False, failure_reason

def main():
    """Main function to run the application."""
    # Initialize logging file header if it doesn't exist
    if not os.path.exists(LOG_FILE):
         with open(LOG_FILE, mode="x", newline="", encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["PhoneNumber", "Message", "Status", "FailureReason"])

    excel_file = get_excel_file()
    contacts_df = read_contacts(excel_file)

    if contacts_df is not None:
        with PreventSleep():
            driver = initialize_driver()
            if driver:
                for index, row in contacts_df.iterrows():
                    first_name = row.get('First name', '')
                    last_name = row.get('Last name', '')
                    phone_number = row.get('Telephone number')
                    message = row.get('Message', '')

                    if pd.isna(phone_number) or not message:
                        print(f"Skipping row {index + 2}: Missing phone number or message.")
                        log_status(str(phone_number), message, "Skipped", "Missing data")
                        continue

                    # Personalize the message
                    personalized_message = message.replace('{first_name}', str(first_name)).replace('{last_name}', str(last_name))

                    print(f"Sending message to {first_name} {last_name} ({phone_number})...")
                    success, status_message = send_whatsapp_message(driver, phone_number, personalized_message)

                    if success:
                        print(f"Message sent to {phone_number}")
                        log_status(phone_number, personalized_message, "Success")
                    else:
                        print(f"Failed to send message to {phone_number}: {status_message}")
                        log_status(phone_number, personalized_message, "Failure", status_message)

                    # Random delay between messages
                    delay_seconds = random.uniform(10, 15)
                    print(f"Waiting for {int(delay_seconds)} seconds before sending the next message...")
                    time.sleep(delay_seconds)

                driver.quit()
                print(f"\nFinished sending messages. Check '{LOG_FILE}' for details.")

if __name__ == "__main__":
    main()
