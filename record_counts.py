import gdata.spreadsheets.client
import os

from counts import calculate_burnup

BURNUP_CHART_SPREADSHEET_KEY="1_xGPZ81Va06pbcclgW7wqsO-pjR_VlU0ZE9mxyzAbmM"
DEFAULT_WORKSHEET_ID = 'od6'

def upload_historical(client, since_days_ago):
    counts = calculate_burnup(since_days_ago=since_days_ago)
    for date in sorted(counts.keys()):
        # Must specify spreadsheet headers as lowercase, silly Google API
        entry = gdata.spreadsheets.data.ListEntry()
        entry.from_dict({"date": date.isoformat(),
                "total": "%d" % counts[date]['total'],
                "closed": "%d" % counts[date]['closed']})
        client.add_list_entry(entry, BURNUP_CHART_SPREADSHEET_KEY, DEFAULT_WORKSHEET_ID)
        print("Uploaded data for %s" % date.isoformat())

def upload_today(client):
    upload_historical(client, 1)

if __name__ == '__main__':
    client = gdata.spreadsheets.client.SpreadsheetsClient()
    client.debug = False
    client_id=os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    client_secret=os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
    scope='https://spreadsheets.google.com/feeds/'
    user_agent='myself'
    token = gdata.gauth.OAuth2Token(client_id=client_id,
            client_secret=client_secret,scope=scope,user_agent=user_agent)
    token.access_token = os.environ.get('GOOGLE_OAUTH_ACCESS_TOKEN')
    token.authorize(client)

    upload_today(client)
