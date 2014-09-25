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

api = asana.AsanaAPI(os.environ.get('ASANA_API_KEY'), debug=True)

WORKSPACE = None
def load_workspace():
    global WORKSPACE
    if WORKSPACE is None:
        for workspace_attrs in api.list_workspaces():
            if workspace_attrs['name'] == WORKSPACE_NAME:
                WORKSPACE = workspace_attrs
    return WORKSPACE

PROJECTS = None
def list_projects(workspace, include_archived=False, filters=None):
    global PROJECTS
    if PROJECTS is None:
        if include_archived:
            include_archived = "true"
        else:
            include_archived = "false"
        target = "projects?archived=%s" % (include_archived)
        if workspace:
            target = "workspaces/%d/" % (workspace) + target
        if filters:
            target += "&opt_fields=%s" % build_filter_for_fields(filters)
        PROJECTS = api._asana(target)
    return PROJECTS

TEAMS = None
def load_team(workspace, team_name=None):
    global TEAMS
    if TEAMS is None:
        TEAMS = {}
        teams = api.organization_teams(workspace['id'])
        for team in teams:
            TEAMS[team['name']] = team
    return TEAMS[team_name]

def load_projects(workspace, team_name=None):
    projects = []
    team = load_team(workspace, team_name)
    for project in list_projects(workspace['id'], include_archived=False,
            filters=['name', 'team']):
        if team is None or project['team']['id'] == team['id']:
            projects.append(project)
    return projects

def get_project_tasks(project, filters=None, include_archived=False):
    if 'tasks' not in project:
        if include_archived:
            include_archived = "true"
        else:
            include_archived = "false"
        target = 'projects/%d/tasks?include_archived=%s'
        if filters:
            target += "&opt_fields=%s" % build_filter_for_fields(filters)
        project['tasks'] = api._asana(target % (project['id'], include_archived))
    return project['tasks']

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

def filter_tasks(tasks, before_date=None, after_date=None):
    for task in tasks:
        task_creation_date = dateutil.parser.parse(task['created_at']).date()
        if ((before_date is None or task_creation_date <= before_date)
                and (after_date is None or task_creation_date >= after_date)):
            yield task

def calculate_burnup(since_days_ago=14):
    workspace = load_workspace();
    projects = load_projects(workspace, TEAM)
    for project in projects:
        project['tasks'] = load_tasks_for_project(project)

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

TAGS = None
def load_tag(workspace, tag_name):
    global TAGS
    if TAGS is None:
        TAGS = {}
        tags = api.get_tags(workspace['id'])
        for tag in tags:
            TAGS[tag['name']] = tag
    return TAGS[tag_name]

all_tasks = {}
def get_task_lazy(task_id):
    if task_id not in all_tasks:
        all_tasks[task_id] = api.get_task(task_id)
    return all_tasks[task_id]

def build_filter_for_fields(filters):
    fkeys = [x.strip().lower() for x in filters]
    fields = ",".join(fkeys)
    return fields

TAG_TASKS = {}
def get_tag_tasks(tag, filters=None):
    if tag['name'] not in TAG_TASKS:
        target = 'tags/%d/tasks'
        if filters:
            target += "?opt_fields=%s" % build_filter_for_fields(filters)
        TAG_TASKS[tag['name']] = api._asana(target % tag['id'])
    return TAG_TASKS[tag['name']]

def calculate_stats(on_date=None):
    workspace = load_workspace()

    if on_date:
        on_date = pytz.UTC.localize(datetime.combine(on_date,
            datetime.min.time()))
    else:
        on_date = datetime.utcnow()
    week_ago = datetime.combine(on_date - timedelta(days=7),
            datetime.min.time())
    week_ago = pytz.UTC.localize(week_ago)

    bugs = []
    bugs = [bug for bug in get_tag_tasks(load_tag(workspace, "Bug"),
                filters=['completed', 'completed_at', 'created_at'])
            if dateutil.parser.parse(bug['created_at']) <= on_date]

    open_bugs = [bug for bug in bugs if not bug['completed']]
    opened_in_last_week = [bug for bug in bugs
            if not bug['completed'] and dateutil.parser.parse(bug['created_at']) >= week_ago]

    closed_in_last_week = [bug for bug in bugs
            if bug['completed'] and dateutil.parser.parse(bug['completed_at']) >= week_ago]

    p1 = [task for task in get_tag_tasks(load_tag(workspace, "P1"),
                filters=['completed', 'completed_at', 'created_at'])
            if not task['completed'] and dateutil.parser.parse(task['created_at']) <= on_date]
    p2 = [task for task in get_tag_tasks(load_tag(workspace, "P2"),
                filters=['completed', 'completed_at', 'created_at'])
            if not task['completed'] and dateutil.parser.parse(task['created_at']) <= on_date]
    p3 = [task for task in get_tag_tasks(load_tag(workspace, "P3"),
                filters=['completed', 'completed_at', 'created_at'])
            if not task['completed'] and dateutil.parser.parse(task['created_at']) <= on_date]

    projects = load_projects(workspace, TEAM)
    security_tasks = []
    ota_tasks = []
    quick_sync_tasks = []
    for project in projects:
        if project['name'] == "Security":
            security_tasks = [task for task in load_tasks_for_project(project)
                if not task['completed'] and dateutil.parser.parse(task['created_at']) <= on_date]
        elif project['name'] == "OTA Firmware Updates":
            ota_tasks = [task for task in load_tasks_for_project(project)
                if not task['completed'] and dateutil.parser.parse(task['created_at']) <= on_date]
        elif project['name'] == "Quick Sync":
            quick_sync_tasks = [task for task in load_tasks_for_project(project)
                if not task['completed'] and dateutil.parser.parse(task['created_at']) <= on_date]

    return {'bugs': len(open_bugs),
                'bugs_closed_in_last_week': len(closed_in_last_week),
                'bugs_opened_in_last_week': len(opened_in_last_week),
                'p1': len(p1),
                'p2': len(p2),
                'p3': len(p3),
                'security': len(security_tasks),
                'ota': len(ota_tasks),
                'quick_sync': len(quick_sync_tasks)}

if __name__ == '__main__':
    calculate_stats()
