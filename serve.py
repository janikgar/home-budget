#!/usr/bin/env python3

import pandas
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
import psycopg2 as pg
from pprint import pprint

PG_USER = 'jacob'

app = Flask('home_budget')
Bootstrap(app)

def open_conn():
  conn = pg.connect(dbname='homebudget', user=PG_USER)
  curs = conn.cursor()
  return conn, curs

@app.route('/')
def index():
  conn, curs = open_conn()
  curs.execute("SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = 'transactions';")
  headers = curs.fetchall()
  header_list = []
  for header in headers:
    header_list.append(header[0])
  # pprint([header_list])
  pprint(header_list)
  curs.execute('SELECT * FROM transactions ORDER BY date desc;')
  txns = curs.fetchall()
  pprint(txns[0])
  return render_template('tables.html', headers=header_list, table=txns)