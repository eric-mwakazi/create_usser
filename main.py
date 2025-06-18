#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script reads an Excel file containing user data,
processes the data, and sends it to a specified API endpoint to create users in a database.
It handles errors and logs the results of each API call.
"""

import random
from time import sleep
import pandas as pd
import requests
import logging
from requests.exceptions import RequestException
from dotenv import load_dotenv
import os
load_dotenv()

#Configs
#===== TESTING in Localhost=====
BASE_URL="http://localhost:19081"
#===== PRODUCTION =====
# BASE_URL = "https://staging.hillcroftinsurance.com"
# API_URL = f"{BASE_URL}/core/createuser"

logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
SKEY = os.getenv("SKEY")
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "SKEY": SKEY
}

agents_file_path = "agents.xlsx"

def read_and_clean_excel(agents_file_path):
    """
    Reads Excel file, cleans column names, and returns DataFrame.
    """
    try:
        df = pd.read_excel(agents_file_path)
        df.columns = (
            df.columns
            .str.replace('\n', ' ')
            .str.strip()
            .str.replace(' ', '')
            .str.replace('_', '')
            .str.upper()
        )
        # Clean and format PHONE column to E.164 format
        if ("PHONE" not in df.columns):
            dummy = f"+2547{random.randint(10000000, 99999999)}"
            df["PHONE"] = dummy

        if "PHONE" in df.columns:
            df["PHONE"] = df["PHONE"]\
                .astype(str).str.replace(r"[^\d]", "", regex=True)
            df["PHONE"] = df["PHONE"]\
                .apply(lambda x: f"+254{x[-9:]}"
                       if x.startswith("7") or len(x) >= 9 else f"+254{x}")
        return df
    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")
        raise

def prepare_agents_payload(df):
    """
    Loops through the DataFrame and prints JSON payloads.
    """
    payloads = []
    for i, row in df.iterrows():
        payload = {
            "name": row["SALESPERSON"],
            "role": row["ROLE"],
            "phone": str(row["PHONE"]),
            "email": row["EMAIL"],
            "agency": {
                "debitNumber": row["SALESCODE"],
                "branchName": row["BRANCH"],
            }
        }
        payloads.append(payload)
    return payloads

def create_user(payload):
    """
    Sends a POST request to the API endpoint with the payload.
    Returns (success: bool, email: str) for tracking.
    """
    try:
        response = requests.post(BASE_URL + "/createuser",
                                 headers=headers, json=payload)
        sleep(1)
        try:
            resp_json = response.json()
            status = resp_json.get("Status", 0)
            message = resp_json.get("Message", "")
            email = payload.get("email", "N/A")

            if status == 508 and "EMAIL_EXISTS" in message:
                logging.warning(f"Status: {status} - Email: {email} - Message: {message}")
                logging.warning(f"User already exists -> Skipping")
                return False, email

            if "INVALID_PHONE_NUMBER" in message:
                logging.warning(f"Status: {status} - Email: {email} - Invalid phone: {message}")
                return False, email

            if status != 200:
                logging.error(f"Status: {status} - Email: {email} - Unexpected error: {message}")
                return False, email

            logging.info(f"Status: {status} - User {email} created successfully")
            return True, email

        except ValueError:
            email = payload.get('email', 'N/A')
            logging.error(f"Non-JSON response: for {email} (HTTP {response.status_code}): {response.text}")
            return False, email

    except RequestException as e:
        email = payload.get('email', 'N/A')
        logging.error(f"Request error for {email}: {e}")
        return False, email


def process_payloads(payloads):
    """
    Processes each payload and logs the result.
    Returns a list of failed emails.
    """
    failed_emails = []
    for payload in payloads:
        success, email = create_user(payload)
        if not success:
            failed_emails.append(email)
    return failed_emails
"""
Main function to read the Excel file and prepare payloads.
"""
def main():
    df = read_and_clean_excel(agents_file_path)
    user_payload = prepare_agents_payload(df)
    print(f"\nCreating users.... Please wait...\n")
    logging.info("Starting user creation process")
    logging.info(f"Total users to create: {len(user_payload)}")
    failed_emails = process_payloads(user_payload)
    created_count = len(user_payload) - len(failed_emails)
    logging.info(f"Total users created: {created_count}")
    logging.info(f"Total users failed to be created: {len(failed_emails)}")
    print(f"Users created. Check log file at: {os.path.abspath('app.log')}\n")
    if failed_emails:
        logging.warning("Failed to create the following users:")
        for email in failed_emails:
            logging.warning(email)
    logging.info("User creation process completed.")

"""
Entry point of the script.
"""
if __name__ == "__main__":
    main()