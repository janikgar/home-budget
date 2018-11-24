#!/usr/bin/env python3

import flask
import google.oauth2.credentials
from google_auth_oauthlib import flow
import apiclient.discovery
import os
import json
import pandas as pd

from config import settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
URL = 'https://sheets.googleapis.com/v4/spreadsheets/' + settings.SPREADSHEET_ID

app = flask.Flask(__name__)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def log(x, end='\n'):
    print(x, end=end)

def sheets_to_df(service, ssid):
    return return_values

def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

@app.route("/")
def index():
    return flask.redirect(flask.url_for('data'))

@app.route("/authorize")
def authorize():
    auth_flow = flow.Flow.from_client_secrets_file("config/oauth2.json", scopes=SCOPES)
    auth_flow.redirect_uri = flask.url_for("oauth2callback", _external=True)
    auth_url, state = auth_flow.authorization_url(access_type="online", include_granted_scopes="true")
    flask.session['state'] = state
    return flask.redirect(auth_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = flask.session['state']
    auth_flow = flow.Flow.from_client_secrets_file("config/oauth2.json", scopes=SCOPES, state=state)
    auth_flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    auth_response = flask.request.url
    auth_flow.fetch_token(authorization_response=auth_response)

    credentials = auth_flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    log("New token saved")
    return flask.redirect(flask.url_for('data'))

@app.route('/data')
def data():
    if 'credentials' not in flask.session:
        return flask.redirect("authorize")
    credentials = google.oauth2.credentials.Credentials(**flask.session['credentials'])
    service = apiclient.discovery.build('sheets', 'v4', credentials=credentials)
    # dfs = sheets_to_df(service, settings.SPREADSHEET_ID)
    log("Getting sheet values:")
    return_values = {}
    for range_string in settings.SHEET_NAMES:
        log("\t {}... ".format(range_string), end="")
        request = service.spreadsheets().values().get(spreadsheetId=settings.SPREADSHEET_ID, range=range_string)
        response = request.execute()
        values = response['values']
        return_values[range_string] = pd.DataFrame(values).head().to_html()
        log("done")
    dfs = return_values
    # flask.session['credentials'] = credentials
    # print((dfs['Transactions']))
    return dfs['Transactions']

app.secret_key = os.urandom(24)
