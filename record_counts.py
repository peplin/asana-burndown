import keen

from counts import count_tasks

if __name__ == '__main__':
    total_tasks, total_open_tasks = count_tasks()
    keen.add_event("task_counts", {
        "total": total_tasks,
        "open": total_open_tasks,
        "closed": total_tasks - total_open_tasks
    })
