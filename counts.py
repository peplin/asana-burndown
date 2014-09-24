#!/usr/bin/env python
from __future__ import division, print_function

import os
from datetime import datetime, timedelta
import dateutil.parser
import collections
import pytz

from asana import asana

WORKSPACE_NAME = os.environ.get("ASANA_WORKSPACE")
TEAM = os.environ.get("ASANA_TEAM")

api = asana.AsanaAPI(os.environ.get('ASANA_API_KEY'), debug=False)

def load_workspace():
    workspace = None
    for workspace_attrs in api.list_workspaces():
        if workspace_attrs['name'] == WORKSPACE_NAME:
            workspace = workspace_attrs
    return workspace

def list_projects(workspace, include_archived=False, filters=None):
    if include_archived:
        include_archived = "true"
    else:
        include_archived = "false"
    target = "projects?archived=%s" % (include_archived)
    if workspace:
        target = "workspaces/%d/" % (workspace) + target
    if filters:
        target += "&opt_fields=%s" % build_filter_for_fields(filters)
    return api._asana(target)

def load_team(workspace, team_name=None):
    for team in api.organization_teams(workspace['id']):
        if team['name'] == team_name:
            return team

def load_projects(workspace, team_name=None):
    projects = []
    team = load_team(workspace, team_name)
    for project in list_projects(workspace['id'], include_archived=False,
            filters=['name', 'team']):
        if team is None or project['team']['id'] == team['id']:
            projects.append(project)
    return projects

def get_project_tasks(project, filters=None, include_archived=False):
    if include_archived:
        include_archived = "true"
    else:
        include_archived = "false"
    target = 'projects/%d/tasks?include_archived=%s'
    if filters:
        target += "&opt_fields=%s" % build_filter_for_fields(filters)
    return api._asana(target % (project['id'], include_archived))

def load_tasks_for_project(project, full=False):
    if full:
        tasks_data = api.get_project_tasks(project['id'])
        tasks = {}
        for task_attrs in tasks_data:
            task_id = task_attrs['id']
            tasks[task_id] = api.get_task(task_id)
        return tasks
    else:
        return get_project_tasks(project,
                filters=['completed', 'completed_at', 'created_at'])

def count_tasks(tasks):
    projects = load_enriched_projects()

    total_tasks = 0
    total_open_tasks = 0
    for project in projects:
        tasks = project['tasks']
        total_tasks += len(tasks)
        open_tasks = [task for task in tasks if not task['completed']]
        total_open_tasks += len(open_tasks)
        closed_tasks = [task for task in tasks if task['completed']]
        print("{:<32} - Open: {:d} Closed: {:d}".format(
            project['name'][:32], len(open_tasks), len(closed_tasks)))
    return total_tasks, total_open_tasks

def filter_tasks(tasks, before_date=None, after_date=None):
    for task in tasks:
        task_creation_date = dateutil.parser.parse(task['created_at']).date()
        if ((before_date is None or task_creation_date <= before_date)
                and (after_date is None or task_creation_date >= after_date)):
            yield task

def load_enriched_projects():
    workspace = load_workspace();
    projects = load_projects(workspace, TEAM)
    for project in projects:
        project['tasks'] = load_tasks_for_project(project)
    return projects

def calculate_burnup(since_days_ago=14):
    projects = load_enriched_projects()

    now = datetime.utcnow()
    now = pytz.UTC.localize(now)
    dates = [(now - timedelta(days=x)).date() for x in range(since_days_ago)]
    counts = collections.defaultdict(dict)
    for date in dates:
        counts[date]['total'] = 0
        counts[date]['closed'] = 0
        for project in projects:
            # Make sure to create a list here, otherwise the generator will be
            # done when you call matching_tasks again to get closed counts
            matching_tasks = list(filter_tasks(project.get('tasks', {}), date))
            counts[date]['total'] += len(matching_tasks)
            counts[date]['closed'] += len([task for task in matching_tasks if task['completed']])
    return counts

def load_tag(workspace, tag_name):
    for tag in api.get_tags(workspace['id']):
        if tag['name'] == tag_name:
            return tag

all_tasks = {}
def get_task_lazy(task_id):
    if task_id not in all_tasks:
        all_tasks[task_id] = api.get_task(task_id)
    return all_tasks[task_id]

def build_filter_for_fields(filters):
    fkeys = [x.strip().lower() for x in filters]
    fields = ",".join(fkeys)
    return fields

def get_tag_tasks(tag, filters=None):
    target = 'tags/%d/tasks'
    if filters:
        target += "?opt_fields=%s" % build_filter_for_fields(filters)
    return api._asana(target % tag['id'])

def calculate_stats():
    workspace = load_workspace()

    bugs = []
    bugs = get_tag_tasks(load_tag(workspace, "Bug"),
            filters=['completed', 'completed_at', 'created_at'])

    now = pytz.UTC.localize(datetime.utcnow())
    week_ago = now - timedelta(days=7)

    open_bugs = [bug for bug in bugs if not bug['completed']]
    opened_in_last_week = [bug for bug in bugs
            if not bug['completed'] and dateutil.parser.parse(bug['created_at']) >= week_ago]

    closed_in_last_week = [bug for bug in bugs
            if bug['completed'] and dateutil.parser.parse(bug['completed_at']) >= week_ago]

    p1 = [task for task in get_tag_tasks(load_tag(workspace, "P1"),
                filters=['completed', 'completed_at', 'created_at'])
            if not task['completed']]
    p2 = [task for task in get_tag_tasks(load_tag(workspace, "P2"),
                filters=['completed', 'completed_at', 'created_at'])
            if not task['completed']]
    p3 = [task for task in get_tag_tasks(load_tag(workspace, "P3"),
                filters=['completed', 'completed_at', 'created_at'])
            if not task['completed']]

    projects = load_projects(workspace, TEAM)
    security_tasks = []
    ota_tasks = []
    quick_sync_tasks = []
    for project in projects:
        if project['name'] == "Security":
            security_tasks = api.get_project_tasks(project['id'])
        elif project['name'] == "OTA Firmware Updates":
            ota_tasks = api.get_project_tasks(project['id'])
        elif project['name'] == "Quick Sync":
            quick_sync_tasks = api.get_project_tasks(project['id'])

    print("Open bugs: %d" % len(open_bugs))
    print("Bugs closed in last 7 days: %d" % len(closed_in_last_week))
    print("Bugs opened in last 7 days: %d" % len(opened_in_last_week))
    print("Open P1 tasks: %d" % len(p1))
    print("Open P2 tasks: %d" % len(p2))
    print("Open P3 tasks: %d" % len(p3))
    print("Open security tasks: %d" % len(security_tasks))
    print("Open OTA tasks: %d" % len(ota_tasks))
    print("Open QuickSync tasks: %d" % len(quick_sync_tasks))


if __name__ == '__main__':
    calculate_stats()
