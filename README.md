# Bulk User Creation Script
This script reads an Excel file containing user data, processes the data, and sends it to a specified API endpoint to create users in a database. It handles errors and logs the results of each API call.

# Requirements
- Python 3.x
- pandas
- requests
# Installation
1. Create a virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```
2. You can install the required packages using pip:
```bash
pip install pandas requests openpyxl python-dotenv or pip install -r requirements.txt
```
# Usage
1. Prepare an Excel file named `agents.xlsx` with the following columns:
   - `SALES CODE`
   - `SALESPERSON`
   - `ROLE`
   - `PHONE`
   - `EMAIL`
2. Place the `agents.xlsx` file in the same directory as the script.
3. Run the script:
```bash
python3 main.py in windows run python main.py
```
# main.py