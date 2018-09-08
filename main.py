#!/usr/bin/env python3

import requests
from google.oauth2 import credentials
import sys
import pickle
import psycopg2 as pg
import re
import datetime
import time

from google_auth_oauthlib import flow
from apiclient.discovery import build

LOG_LOCATION = "console"
# LOG_LOCATION = "logfile"
PG_USER = "jacob"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SPREADSHEET_ID = '1wbnG31Z5QBm2fuyzZOY9XkSij0EERtX92wEHq9LbPiI'
URL = 'https://sheets.googleapis.com/v4/spreadsheets/' + SPREADSHEET_ID
SHEET_NAMES = ["Transactions", "Categories", "Balance History"]
AUTH_FILE_NAME = 'config/oauth2.json'
# AUTH_FILE = json.load(AUTH_FILE_NAME)['installed']

def parse_google_auth(file):
  """
  parse_goole_auth(file)
  :param: file is a String with a path (relative or absolute) to the given JSON file.

  This function requires a JSON file for a specific Google OAuth user.
  This can be received from the Google Cloud Console for the linked project.
  """
  log("Loading Google Sheet... ", end="")
  try:
    saved_token = open('config/token.bin', 'rb')
    creds = pickle.load(saved_token)
    log("Saved token found")
  except FileNotFoundError:
    saved_token = open('config/token.bin', 'wb+')
    auth_flow = flow.InstalledAppFlow.from_client_secrets_file(file, scopes=SCOPES)
    creds = auth_flow.run_local_server(open_browser=True)
    pickle.dump(creds, saved_token)
    log("New token saved")
  finally:
    saved_token.close()

  service = build('sheets', 'v4', credentials=creds)
  return service

def get_sheet_values(service, file_id):
  log("Getting sheet values:")
  return_values = []
  for range_string in SHEET_NAMES:
    log("\t {}... ".format(range_string), end="")
    request = service.spreadsheets().values().batchGet(
        spreadsheetId=SPREADSHEET_ID, ranges=range_string)
    response = request.execute()
    values = response['valueRanges'][0]['values']
    return_values.append(values)
    log("done")
  return return_values

def db_create():
  conn = pg.connect(dbname="postgres", user=PG_USER)
  conn.autocommit = True
  cursor = conn.cursor()
  cursor.execute("CREATE DATABASE homebudget;")

def db_create_tables(conn):
  cursor = conn.cursor()
  cursor.execute("""CREATE TABLE transactions (
    date date,
    description varchar(255),
    category varchar(128),
    amount float,
    note varchar(128),
    account varchar(255),
    account_num varchar(128),
    institution varchar(128),
    month date,
    week date,
    transaction_id varchar(128),
    check_num varchar(128),
    full_description varchar(255),
    added_date date,
    id serial,
    PRIMARY KEY(id)
      );""")
  cursor.execute("CREATE INDEX trans_index ON transactions (date, id)")
  cursor.execute("""CREATE TABLE categories (
    group_name varchar(128),
    category varchar(128),
    type varchar(128),
    report_hidden bool,
    budget float,
    id serial,
    PRIMARY KEY(id)
  );""")
  cursor.execute("CREATE INDEX cat_index ON categories (group_name)")
  cursor.execute(""" CREATE TABLE balance_history (
    date date,
    time timetz,
    account varchar(128),
    account_num varchar(128),
    institution varchar(128),
    balance float,
    month date,
    week date,
    index int,
    type varchar(128),
    class varchar(128),
    id serial,
    PRIMARY KEY(id)
  );
  """)
  cursor.execute("CREATE INDEX bal_index ON balance_history (date, account, account_num, type, class)")
  cursor.close()

def db_check():
  # Create DB if it doesn't exist
  try:
    conn = pg.connect(dbname='homebudget', user=PG_USER)
    conn.autocommit = True
  except pg.OperationalError:
    log("Creating database...", end="")
    db_create()
    conn = pg.connect(dbname='homebudget', user=PG_USER)
    conn.autocommit = True
    log("  done")

  # Create tables if they don't exist
  try:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions LIMIT 1;")
    cursor.execute("SELECT * FROM categories LIMIT 1;")
    cursor.execute("SELECT * FROM balance_history LIMIT 1;")
  except pg.ProgrammingError:
    log("Creating tables...", end="")
    db_create_tables(conn)
    conn.close()
    log("  done")

def db_drop():
  conn = pg.connect(dbname="postgres", user=PG_USER)
  conn.autocommit = True
  curs = conn.cursor()
  try:
    curs.execute("DROP DATABASE homebudget;")
  except:
    pass
  finally:
    curs.close()

def pg_strpdate(datestring):
  this_date = time.strptime(datestring, '%m/%d/%Y')
  return time.strftime("%Y-%m-%d", this_date)

def pg_strptime(timestring):
  this_time = time.strptime(timestring, '%I:%M %p')
  return time.strftime("%T", this_time)

def pg_dollars(dollarstring):
  this_string = re.sub(r'[$,]', "", dollarstring)
  return this_string

def parse_transactions(transactions):
  conn, curs = open_budget_cursor()
  log("Parsing transactions... ", end="")
  i = 0
  for row in transactions:
    if i != 0:
      row[0] = pg_strpdate(row[0])
      row[3] = pg_dollars(row[3])
      row[13] = pg_strpdate(row[13])
      rowtuple = tuple(row)
      curs.execute("""
        INSERT INTO transactions
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
      """, rowtuple)
    i += 1
  conn.commit()
  curs.close()
  log("done")

def log(string, end="\n"):
  if LOG_LOCATION == "console":
    print(string, end=end)
  elif LOG_LOCATION == "logfile":
    logfile = open('data/logfile.txt', 'a+')
    logfile.writelines(string + end)
    logfile.close()

def parse_categories(categories):
  conn, curs = open_budget_cursor()
  log("Parsing categories... ", end="")
  i = 0
  for row in categories:
    while len(row) < 5:
      row.append("")
    if i != 0:
      if row[3] == "Hide":
        row[3] = True
      else:
        row[3] = False
      if row[4] == "":
        row[4] = "0"
      row[4] = pg_dollars(row[4])
      rowtuple = tuple(row)
      curs.execute("""
        INSERT INTO categories
        VALUES (%s, %s, %s, %s, %s)
      """, rowtuple)
    i += 1
  conn.commit()
  curs.close()
  log("done")

def parse_balance_history(balance_history):
  conn, curs = open_budget_cursor()
  log("Parsing balance history... ", end="")
  i = 0
  for row in balance_history:
    if i != 0:
      row[0] = pg_strpdate(row[0])
      row[1] = pg_strptime(row[1])
      row[5] = pg_dollars(row[5])
      if row[8] == "":
        row[8] = "0"
      rowtuple = tuple(row)
      curs.execute("""
        INSERT INTO balance_history
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
      """, rowtuple)
    i += 1
  conn.commit()
  curs.close()
  log("done")

def open_budget_cursor():
  conn = pg.connect(dbname='homebudget', user=PG_USER)
  curs = conn.cursor()
  return conn, curs

def update():
  db_drop()
  db_check()
  service = parse_google_auth(AUTH_FILE_NAME)
  transactions, categories, balance_history = get_sheet_values(service, SPREADSHEET_ID)
  parse_transactions(transactions)
  transactions = None
  parse_categories(categories)
  categories = None
  parse_balance_history(balance_history)
  balance_history = None

def run():
  pass
  
if __name__ == "__main__":
  if LOG_LOCATION == "logfile":
    logfile = open('data/logfile.txt', 'w+')
    logfile.write('')
    logfile.close()
  if ("-u" in sys.argv) or ("--update" in sys.argv):
    update()
  if ("-s" in sys.argv) or ("--serve" in sys.argv):
    pass
  # run()
