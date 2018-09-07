#!/usr/bin/env python3

import requests
import pandas
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from google.oauth2 import credentials
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
import json
from google.auth.transport.requests import AuthorizedSession
from pprint import pprint as pp
import pickle
import psycopg2 as pg
import re
import datetime
import time

from google_auth_oauthlib import flow
from apiclient.discovery import build

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

  try:
    saved_token = open('config/token.bin', 'rb')
    creds = pickle.load(saved_token)
  except FileNotFoundError:
    saved_token = open('config/token.bin', 'wb+')
    auth_flow = flow.InstalledAppFlow.from_client_secrets_file(file, scopes=SCOPES)
    creds = auth_flow.run_local_server(open_browser=True)
    pickle.dump(creds, saved_token)
  finally:
    saved_token.close()

  service = build('sheets', 'v4', credentials=creds)
  return service

def open_file(service, file_id, range_string):
  request = service.spreadsheets().values().batchGet(
      spreadsheetId=SPREADSHEET_ID, ranges=range_string)
  response = request.execute()
  filename = re.sub(r'\s+', '_', range_string.lower())
  savefile = open('data/{}.json'.format(filename), 'w+')
  json.dump(response, savefile, indent=4, separators=[',', ': '])

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
    category varchar(255),
    amount float,
    note varchar(255),
    account varchar(255),
    account_num varchar(255),
    institution varchar(255),
    month date,
    week date,
    transaction_id varchar(255),
    check_num varchar(255),
    full_description varchar(255),
    added_date date,
    id serial,
    PRIMARY KEY(id)
      );""")
  cursor.execute("CREATE INDEX trans_index ON transactions (date, id)")
  cursor.execute("""CREATE TABLE categories (
    group_name varchar(64),
    category varchar(64),
    type varchar(64),
    report_hidden bool,
    budget int,
    id serial,
    PRIMARY KEY(id)
  );""")
  cursor.execute("CREATE INDEX cat_index ON categories (group_name)")
  cursor.execute(""" CREATE TABLE balance_history (
    date date,
    time timetz,
    account varchar(64),
    account_num varchar(64),
    institution varchar(64),
    balance float,
    month date,
    week date,
    index int,
    type varchar(64),
    class varchar(64),
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
    print("Creating database...", end="")
    db_create()
    conn = pg.connect(dbname='homebudget', user=PG_USER)
    conn.autocommit = True
    print("  done")

  # Create tables if they don't exist
  try:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions LIMIT 1;")
    cursor.execute("SELECT * FROM categories LIMIT 1;")
    cursor.execute("SELECT * FROM balance_history LIMIT 1;")
  except pg.ProgrammingError:
    print("Creating tables...", end="")
    db_create_tables(conn)
    conn.close()
    print("  done")

def parse_transactions():
  conn = pg.connect(dbname='homebudget', user=PG_USER)
  conn.autocommit = True
  curs = conn.cursor()
  this_json = json.load(open("data/transactions.json"))
  rows = this_json['valueRanges'][0]['values']
  i = 0
  for row in rows:
    if i != 0:
      # joiner = ', '
      row[0] = pg_strptime(row[0])
      row[3] = pg_dollars(row[3])
      row[13] = pg_strptime(row[13])
      # print(row)
      rowtuple = tuple(row)
      # print(rowtuple)
      curs.execute("""
        INSERT INTO transactions
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
      """, rowtuple)
    i += 1

def pg_strptime(datestring):
  this_time = time.strptime(datestring, '%m/%d/%Y')
  return time.strftime("%Y-%m-%d", this_time)

def pg_dollars(dollarstring):
  this_string = re.sub(r'[$,]', "", dollarstring)
  return this_string
   

# def parse_categories():
#   pass

# def parse_balance_history():
#   pass

def parse_files_to_db():
  parse_transactions()
  # parse_categories()
  # parse_balance_history()

def run():
  db_check()
  service = parse_google_auth(AUTH_FILE_NAME)
  for range_string in SHEET_NAMES:
    open_file(service, SPREADSHEET_ID, range_string)
  parse_files_to_db()
  
if __name__ == "__main__":
  run()
  # parse_files_to_db()