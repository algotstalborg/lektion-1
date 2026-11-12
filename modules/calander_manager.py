import calendar
from datetime import date, datetime, timedelta

from modules.storage import load_tasks


def get_month_days(year, month, week_start="monday"):
    cal = calendar.Calendar(
        firstweekday=(
            calendar.MONDAY
            if week_start == "monday"
            else calendar.SUNDAY
        )
    )

    return cal.monthdatescalendar(year, month)


def get_tasks_for_date(target_date):
    if isinstance(target_date, date):
        target_date = target_date.isoformat()

    return sorted(
        [
            task for task in load_tasks()
            if task.get("date") == target_date
            and not task.get("archived", False)
        ],
        key=lambda task: task.get("time", "00:00")
    )


def get_tasks_for_month(year, month):
    prefix = f"{year:04d}-{month:02d}"

    return [
        task for task in load_tasks()
        if task.get("date", "").startswith(prefix)
        and not task.get("archived", False)
    ]


def get_upcoming_tasks(days=7):
    today = date.today()
    end_date = today + timedelta(days=days)

    tasks = [
        task for task in load_tasks()
        if not task.get("archived", False)
        and today.isoformat() <= task.get("date", "")
        <= end_date.isoformat()
    ]

    return sorted(
        tasks,
        key=lambda task: (
            task.get("date", ""),
            task.get("time", "")
        )
    )


def get_week_dates(target_date=None):
    target_date = target_date or date.today()

    monday = target_date - timedelta(
        days=target_date.weekday()
    )

    return [
        monday + timedelta(days=i)
        for i in range(7)
    ]


def get_month_name(year, month):
    months = [
        "Januari", "Februari", "Mars",
        "April", "Maj", "Juni",
        "Juli", "Augusti", "September",
        "Oktober", "November", "December"
    ]

    return f"{months[month - 1]} {year}"


def is_today(target_date):
    return target_date == date.today()