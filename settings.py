# Choose to send logs to console or logfile
LOG_LOCATION = "console"
# LOG_LOCATION = "logfile"

# Enter the username for PostgreSQL. Needs permission to create the database
PG_USER = "jacob"

# The Google Sheets ID for your Tiller sheet
SPREADSHEET_ID = '1wbnG31Z5QBm2fuyzZOY9XkSij0EERtX92wEHq9LbPiI'

# Names of your Tiller sheets. Requires the first to be the transaction register, the second the category listing, and the third the balance history
SHEET_NAMES = ["Transactions", "Categories", "Balance History"]

# Location of the OAuth2 setting
AUTH_FILE_NAME = 'config/oauth2.json'
