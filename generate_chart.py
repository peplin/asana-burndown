import os
import matplotlib.pyplot as plt

from counts import load_workspace, load_projects, load_tasks_for_project, \
        calculate_burnup

WORKSPACE_NAME = os.environ.get("ASANA_WORKSPACE")
TEAM = os.environ.get("ASANA_TEAM")

def generate_chart(counts):
    dates = [date for date in sorted(counts.keys())]
    totals = [counts[date]['total'] for date in dates]
    closeds = [counts[date]['closed'] for date in dates]

    plt.plot(dates, totals, 'r-', dates, closeds, 'b-')
    plt.ylabel('Burnup')
    plt.xlabel('Date')
    plt.show()

if __name__ == '__main__':
    counts = calculate_burnup(since_days_ago=14)
    generate_chart(counts)
