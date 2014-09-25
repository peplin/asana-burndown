import gdata.spreadsheets.client
import os

from counts import calculate_burnup, calculate_stats

BURNUP_CHART_SPREADSHEET_KEY="1_xGPZ81Va06pbcclgW7wqsO-pjR_VlU0ZE9mxyzAbmM"
DEFAULT_WORKSHEET_ID = 'od6'

def upload_historical(client, since_days_ago):
    counts = calculate_burnup(since_days_ago=since_days_ago)
    for date in sorted(counts.keys()):
        stats = calculate_stats(on_date=date)
        # Must specify spreadsheet headers as lowercase, silly Google API
        entry = gdata.spreadsheets.data.ListEntry()
        data = {'date': date.isoformat(),
                'total': "%d" % counts[date]['total'],
                'closed': "%d" % counts[date]['closed'],
                'bugs': "%d" % stats['bugs'],
                'bugsclosedinlastweek': "%d" % stats['bugs_closed_in_last_week'],
                'bugsopenedinlastweek': "%d" % stats['bugs_opened_in_last_week'],
                'p1': "%d" % stats['p1'],
                'p2': "%d" % stats['p2'],
                'p3': "%d" % stats['p3'],
                'security': "%d" % stats['security'],
                'ota': "%d" % stats['ota'],
                'quicksync': "%d" % stats['quick_sync']}
        entry.from_dict(data)
        client.add_list_entry(entry, BURNUP_CHART_SPREADSHEET_KEY, DEFAULT_WORKSHEET_ID)
        print("Uploaded data for %s" % date.isoformat())

def upload_today(client):
    upload_historical(client, 1)

if __name__ == '__main__':
    client = gdata.spreadsheets.client.SpreadsheetsClient()
    client.debug = True
    client_id=os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    client_secret=os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
    scope='https://spreadsheets.google.com/feeds/'
    user_agent='myself'
    token = gdata.gauth.OAuth2Token(client_id=client_id,
            client_secret=client_secret,scope=scope,user_agent=user_agent)
    token.access_token = os.environ.get('GOOGLE_OAUTH_ACCESS_TOKEN')
    token.refresh_token = os.environ.get('GOOGLE_OAUTH_REFRESH_TOKEN')
    token.authorize(client)

    # upload_today(client)
    upload_historical(client, 7*16)
