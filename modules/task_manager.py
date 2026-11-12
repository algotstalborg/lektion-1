from datetime import datetime, timedelta
from uuid import uuid4

from modules.storage import load_tasks, save_tasks


def create_task(
    name,
    category,
    date,
    time,
    priority,
    description="",
    notes="",
    reminder=None,
    recurrence="none"
):
    task = {
        "id": str(uuid4()),
        "name": name,
        "category": category,
        "date": date,
        "time": time,
        "priority": priority,
        "description": description,
        "notes": notes,
        "reminder": reminder,
        "recurrence": recurrence,
        "archived": False,
        "series_id": None,
        "created": datetime.now().isoformat(),
        "reminded": False
    }

    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)

    return task


def update_task(task_id, changes):
    tasks = load_tasks()

    for task in tasks:
        if task["id"] == task_id:
            task.update(changes)

            if "reminded" not in changes:
                task["reminded"] = False

            break

    save_tasks(tasks)


def delete_task(task_id):
    tasks = load_tasks()

    tasks = [
        task for task in tasks
        if task["id"] != task_id
    ]

    save_tasks(tasks)


def filter_tasks(category=None, priority=None):
    tasks = load_tasks()

    result = [
        task for task in tasks
        if not task.get("archived", False)
    ]

    if category:
        result = [
            task for task in result
            if task["category"] == category
        ]

    if priority:
        result = [
            task for task in result
            if task["priority"] == priority
        ]

    return sorted(
        result,
        key=lambda task: (
            task["date"],
            task["time"]
        )
    )


def archive_old_tasks():
    tasks = load_tasks()
    today = datetime.now()

    for task in tasks:
        if task.get("archived", False):
            continue

        try:
            deadline = datetime.strptime(
                task["date"] + " " + task["time"],
                "%Y-%m-%d %H:%M"
            )
        except (ValueError, KeyError):
            continue

        if today >= deadline + timedelta(days=7):
            task["archived"] = True

    save_tasks(tasks)


def restore_task(task_id):
    tasks = load_tasks()

    for task in tasks:
        if task["id"] == task_id:
            task["archived"] = False

    save_tasks(tasks)


def get_archived_tasks():
    return [
        task for task in load_tasks()
        if task.get("archived", False)
    ]
