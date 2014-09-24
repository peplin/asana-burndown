import keen
from datetime import datetime

from counts import calculate_burnup

def upload_historical(since_days_ago):
    counts = calculate_burnup(since_days_ago=since_days_ago)
    events = [{"total": counts[date]['total'],
                    "closed": counts[date]['closed'],
                    "open": counts[date]['total'] - counts[date]['closed'],
                    'keen': {
                        'timestamp': date.isoformat()
                    }}
                for date in sorted(counts.keys())]
    keen.add_events({"task_counts": events})

def upload_today():
    upload_historical(0)

if __name__ == '__main__':
    upload_historical(7*16)
