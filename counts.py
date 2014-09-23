#!/usr/bin/env python
from __future__ import division, print_function

import os

from prettyprint import pp
from asana import asana

WORKSPACE_NAME = os.environ.get("ASANA_WORKSPACE")
TEAM = os.environ.get("ASANA_TEAM")

api = asana.AsanaAPI(os.environ.get('ASANA_API_KEY'), debug=False)

workspace = None
for workspace_attrs in api.list_workspaces():
    if workspace_attrs['name'] == WORKSPACE_NAME:
        workspace = workspace_attrs

projects = {}
for project_attrs in api.list_projects(workspace['id'], include_archived=False):
    project = api.get_project(project_attrs['id'])
    if project['team']['name'] == TEAM:
        projects[project['id']] = project
        break

for project in projects.values():
    tasks = api.get_project_tasks(project['id'])
    project['tasks'] = {}
    for task_attrs in tasks:
        task_id = task_attrs['id']
        project['tasks'][task_id] = api.get_task(task_id)

total_tasks = 0
total_open_tasks = 0
for project in projects.values():
    tasks = project.get('tasks', {}).values()
    total_tasks += len(tasks)
    open_tasks = [task for task in tasks if not task['completed']]
    total_open_tasks += len(open_tasks)
    closed_tasks = [task for task in tasks if task['completed']]
    print("{:<32} - Open: {:d} Closed: {:d}".format(
        project['name'][:32], len(open_tasks), len(closed_tasks)))

print("Total Tasks: %d" % total_tasks)
print("Total Open Tasks: %d" % total_open_tasks)
print("Completion: %f%%" % ((total_tasks - total_open_tasks) / total_tasks))
