#!/usr/bin/env python3

import pandas as pd
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
import psycopg2 as pg
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.offline as offline
import numpy as np
import cufflinks as cf
import datetime

PG_USER = 'jacob'
CONN = pg.connect(dbname="homebudget", user=PG_USER)

app = Flask('home_budget')
Bootstrap(app)

def net_worth():
  balance_data = pd.read_sql("SELECT date, balance, account FROM balance_history ORDER BY date ASC", con=CONN, index_col=["date"])
  idx = balance_data.index.unique()
  cols = balance_data['account'].unique()
  # return cols
  newb = balance_data.reindex(index=idx, columns=cols)
  # date_index = balance_data.index.unique().tolist()
  # newb = balance_data.pivot(index=idx, columns="account", values="balance")
  return newb
  grouped = balance_data.groupby('account')
  go_data = []
  i = 0
  last_balance = 0
  for name, group in grouped:
    if True:
      this_go_data = go.Scatter(
        x = group['date'],
        y = group['balance'],
        name = name,
        mode = 'lines',
        fill = 'tonexty'
      )
    go_data.append(this_go_data)
    i += 1
  layout = go.Layout(
    showlegend=True,
    title='Balance History'
  )
  fig = go.Figure(data=go_data,layout=layout)
  offline.plot(fig, filename='data/net-worth')

def balance_plot():
  balance_data = pd.read_sql("SELECT date, balance, account FROM balance_history ORDER BY account, date ASC", con=CONN)
  grouped = balance_data.query('date > datetime.date(1971, 1, 1)').groupby('account')
  # grouped.iplot(kind='area', fill=True, filename='cuflinks/stacked-area')
  go_data = []
  for name, group in grouped:
    this_go_data = go.Scatter (
      x = group['date'],
      y = group['balance'],
      name = name
    )
    go_data.append(this_go_data)
  layout = go.Layout(
    title='Balance History',
    xaxis={'title':'time'},
    yaxis={'title':'balance'}
  )
  fig = go.Figure(data=go_data,layout=layout)
  offline.plot(fig, filename='data/balance-history')

def open_curs():
  try:
    conn = CONN
  except UnboundLocalError:
    CONN = pg.connect(dbname='homebudget', user=PG_USER)
    conn = CONN
  curs = conn.cursor()
  return curs

@app.route('/')
def index():
  conn, curs = open_curs()
  curs.execute("SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = 'transactions';")
  headers = curs.fetchall()
  header_list = []
  for header in headers:
    header_list.append(header[0])
  curs.execute('SELECT * FROM transactions ORDER BY date desc;')
  txns = curs.fetchall()
  return render_template('tables.html', headers=header_list, table=txns)
