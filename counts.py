#!/usr/bin/env python
from __future__ import division, print_function

import os

from prettyprint import pp
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

def load_projects(workspace, team=None):
    projects = {}
    for project_attrs in api.list_projects(workspace['id'], include_archived=False):
        project = api.get_project(project_attrs['id'])
        if team is None or project['team']['name'] == team:
            projects[project['id']] = project
    return projects

def load_tasks_for_project(project):
    tasks_data = api.get_project_tasks(project['id'])
    tasks = {}
    for task_attrs in tasks_data:
        task_id = task_attrs['id']
        tasks[task_id] = api.get_task(task_id)
    return tasks

def count_tasks(tasks):
    workspace = load_workspace();
    projects = load_projects(workspace, TEAM)
    for project in projects.values():
        project['tasks'] = load_tasks_for_project(project)

    total_tasks = 0
    total_open_tasks = 0
    for project in projects.values():
        tasks = project['tasks'].values()
        total_tasks += len(tasks)
        open_tasks = [task for task in tasks if not task['completed']]
        total_open_tasks += len(open_tasks)
        closed_tasks = [task for task in tasks if task['completed']]
        print("{:<32} - Open: {:d} Closed: {:d}".format(
            project['name'][:32], len(open_tasks), len(closed_tasks)))
    return total_tasks, total_open_tasks

if __name__ == '__main__':
    total_tasks, total_open_tasks = count_tasks()
    print("Total Tasks: %d" % total_tasks)
    print("Total Open Tasks: %d" % total_open_tasks)
    print("Completion: %f%%" % ((total_tasks - total_open_tasks) / total_tasks))
