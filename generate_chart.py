import os
from datetime import datetime, timedelta
import dateutil.parser
import collections
import pytz
import matplotlib.pyplot as plt

from counts import load_workspace, load_projects, load_tasks_for_project

WORKSPACE_NAME = os.environ.get("ASANA_WORKSPACE")
TEAM = os.environ.get("ASANA_TEAM")

def filter_tasks(tasks, before_date):
    for task in tasks:
        task_creation_date = dateutil.parser.parse(task['created_at'])
        if task_creation_date <= before_date:
            yield task

if __name__ == '__main__':
    workspace = load_workspace();
    projects = load_projects(workspace, TEAM)
    all_tasks = {}
    for project in projects.values():
        project['tasks'] = load_tasks_for_project(project)

    now = datetime.utcnow()
    now = pytz.UTC.localize(now)
    dates = [now - timedelta(days=x) for x in range(14)]
    counts = collections.defaultdict(dict)
    for date in dates:
        counts[date]['total'] = 0
        counts[date]['closed'] = 0
        for project in projects.values():
            # Make sure to create a list here, otherwise the generator will be
            # done when you call matching_tasks again to get closed counts
            matching_tasks = list(filter_tasks(project['tasks'].values(), date))
            counts[date]['total'] += len(matching_tasks)
            counts[date]['closed'] += len([task for task in matching_tasks if task['completed']])

    for date in sorted(counts.keys()):
        print("%s,%d,%d" % (date.isoformat(), counts[date]['total'], counts[date]['closed']))

    dates = [date for date in sorted(counts.keys())]
    totals = [counts[date]['total'] for date in dates]
    closeds = [counts[date]['closed'] for date in dates]
    plt.plot(dates, totals, 'r-', dates, closeds, 'b-')
    plt.ylabel('Burnup')
    plt.xlabel('Date')
    plt.show()
