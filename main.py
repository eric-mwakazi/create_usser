#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script reads an Excel file containing user data,
processes the data, and sends it to a specified API endpoint to create users in a database.
It handles errors and logs the results of each API call.
"""

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
API_URL = f"{BASE_URL}/createuser"
#===== PRODUCTION =====
# BASE_URL = "https://staging.hillcroftinsurance.com/"
# API_URL = f"{BASE_URL}/core/createuser"
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
            .str.replace(' ', '_')
            .str.upper()
        )
        # Clean and format PHONE column to E.164 format
        if "PHONE" in df.columns:
            df["PHONE"] = df["PHONE"].astype(str).str.replace(r"[^\d]", "", regex=True)
            df["PHONE"] = df["PHONE"].apply(lambda x: f"+254{x[-9:]}"
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
                "supplierNumber": row["SALES__CODE"]
            }
        }

        # print(f"\n Payload for USER_NO {i + 1} Name {row['SALESPERSON']}:")
        # print(payload)
        payloads.append(payload)
        #print(payloads)
    return payloads

def create_user(payload):
    """
    Sends a POST request to the API endpoint with the payload.
    Skips if the user already exists.
    Logs or continues on other errors.
    """
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        sleep(1)

        try:
            resp_json = response.json()
            status = resp_json.get("Status", 0)
            message = resp_json.get("Message", "")

            # Check if it's truly "user already exists"
            if status == 508 and "EMAIL_EXISTS" in message:
                print(f"User already exists: {payload['email']} — skipping.")
                return

            # Handle other known issues
            if "INVALID_PHONE_NUMBER" in message:
                print(f"Invalid phone number for {payload['email']}: {message}")
                return

            # Unknown error still logged
            if status != 200:
                print(f"Unexpected error for {payload['email']}: {message}")
                return

            print(f"Created USER: {resp_json}")

        except ValueError:
            print(f"Non-JSON response (status {response.status_code}): {response.text}")

    except RequestException as e:
        print(f"🚨 Request error for {payload['email']}: {e}")


"""
Main function to read the Excel file and prepare payloads.
"""
def main():
    df = read_and_clean_excel(agents_file_path)
    user_payload = prepare_agents_payload(df)

    for payload in user_payload:
        create_user(payload)

"""
Entry point of the script.
"""
if __name__ == "__main__":
    main()