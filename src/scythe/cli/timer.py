import datetime
import time

from arc import Context, namespace
from arc.ui import SelectionMenu
from arc.color import effects

from .. import helpers
from .. import utils
from ..harvest_api import HarvestApi
from ..live_text import LiveText


timer = namespace("timer")


@timer.subcommand()
@utils.config_required
@utils.get_projects
def create(ctx: Context):
    """\
    Creates a timer
    Will also start the timer"""
    api: HarvestApi = ctx.api
    cache: utils.Cache = ctx.cache
    projects: list[helpers.Project] = ctx.projects

    project_idx, _ = utils.exist_or_exit(
        SelectionMenu([project.name for project in projects]).run()
    )
    print()

    project = projects[project_idx]

    task_idx, _ = utils.exist_or_exit(
        SelectionMenu([task.name for task in project.tasks]).run()
    )
    print()

    task = project.tasks[task_idx]

    print(f"{effects.BOLD}Project{effects.CLEAR}: {project.name}")
    print(f"{effects.BOLD}Task{effects.CLEAR}: {task.name}")

    note = input("Note: ")

    res = api.create_timer(project_id=project.id, task_id=task.id, notes=note)

    utils.print_valid_response(res, "Timer Started!")
    cache["running_timer"] = res.json()["id"]
    cache.save()


@timer.subcommand()
@utils.config_required
def running(ctx: Context, interval: int = 10):
    """\
    Displays the currently running timer

    Arguments:
    interval=VALUE Interval in seconds which to refresh data
                   by calling the API. Defaults to 10
    """
    api: HarvestApi = ctx.api
    entry = api.get_running_timer()
    if not entry:
        print("No running timer")
        return

    entry = helpers.TimeEntry(entry)
    hours, minutes = utils.parse_time(entry.hours)
    format_str = (
        "Time Spent: {hours} \n Project: {project_name}\n"
        " Task: {task_name}\n Notes: {notes}"
    )
    text = LiveText(
        format_str.format(
            hours=f"{hours}:{minutes}",
            project_name=entry.project["name"],
            task_name=entry.task["name"],
            notes=entry.notes,
        )
    )

    while True:
        entry = api.get_running_timer()
        if not entry:
            print("Timer stopped running")
            return

        entry = helpers.TimeEntry(entry)
        hours, minutes = utils.parse_time(entry.hours)

        text.update(
            format_str.format(
                hours=utils.format_time(hours, minutes),
                project_name=entry.project["name"],
                task_name=entry.task["name"],
                notes=entry.notes,
            )
        )

        time.sleep(interval)


@timer.subcommand()
@utils.config_required
def start(cached: bool, ctx: Context):
    """Start a previously created timer.

    Arguments:
    --cached   Will check the cache for an
               running_timer and start that timer
    """
    api: HarvestApi = ctx.api
    cache: utils.Cache = ctx.cache

    entry_id = None
    if cached:
        entry_id = cache["running_timer"]

    if not entry_id:
        print("Fetching timers from today...")
        entries = api.get(f"/time_entries?from={datetime.date.today()}").json()[
            "time_entries"
        ]
        entries = helpers.TimeEntry.from_list(entries)
        entry_idx, _ = utils.pick_time_entry(entries)
        entry_id = entries[entry_idx].id
        cache["running_timer"] = entry_id
        cache.save()

    res = api.patch(f"/time_entries/{entry_id}/restart")
    utils.print_valid_response(res, "Timer Started!")


@timer.subcommand()
@utils.config_required
def stop(cached: bool, ctx: Context):
    """Stops a running timer.

    Arguments:
    --cached  Will check the cache
              for an running_timer and stop that timer
    """
    api: HarvestApi = ctx.api
    cache: utils.Cache = ctx.cache

    entry_id = None
    if cached:
        entry_id = cache["running_timer"]

    if not entry_id:
        print("Checking Harvest for running timers...")
        entry = api.get_running_timer()
        if not entry:
            print("No running timers")
            return

        entry_id = entry["id"]

    res = api.patch(
        f"/time_entries/{entry_id}/stop",
    )
    utils.print_valid_response(res, "Timer Stopped!")
    cache["running_timer"] = entry_id
    cache.save()


@timer.subcommand()
@utils.config_required
def delete(cached: bool, ctx: Context):
    """Used to delete a timer from the current day's list

    Arguments:
    --cached  Will check the cache
              for an running_timer and delete that timer
    """

    api: HarvestApi = ctx.api
    cache: utils.Cache = ctx.cache

    entry_id = None
    if cached:
        entry_id = cache["running_timer"]

    if not entry_id:
        payload = {"from": str(datetime.date.today())}
        print("Fetching timers from today...")
        entries = api.get("/time_entries", params=payload).json()["time_entries"]

        entries = helpers.TimeEntry.from_list(entries)
        entry_idx, _ = utils.pick_time_entry(entries)
        entry_id = entries[entry_idx].id

    res = api.delete(f"/time_entries/{entry_id}")
    utils.print_valid_response(res, "Timer Deleted")
