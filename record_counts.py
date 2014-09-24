import gdata.spreadsheet.service
import getpass

from counts import calculate_burnup

BURNUP_CHART_SPREADSHEET_KEY="1_xGPZ81Va06pbcclgW7wqsO-pjR_VlU0ZE9mxyzAbmM"
DEFAULT_WORKSHEET_ID = 'od6'

def upload_historical(since_days_ago):
    counts = calculate_burnup(since_days_ago=since_days_ago)
    for date in sorted(counts.keys()):
        # Must specify spreadsheet headers as lowercase, silly Google API
        row = {"date": date.isoformat(),
                "total": "%d" % counts[date]['total'],
                "closed": "%d" % counts[date]['closed']}
        client.InsertRow(row, BURNUP_CHART_SPREADSHEET_KEY, DEFAULT_WORKSHEET_ID)
        print("Uploaded data for %s" % date.isoformat())

def upload_today():
    upload_historical(1)

if __name__ == '__main__':
    client = gdata.spreadsheet.service.SpreadsheetsService()
    client.debug = False
    client.email = raw_input("Google Email: ")
    client.password = getpass.getpass()
    client.source = 'some description'
    client.ProgrammaticLogin()

    upload_today()
