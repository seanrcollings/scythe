import datetime

from arc import Context, namespace
from arc.color import effects, fg

from .. import helpers
from .. import utils
from .. import decos
from ..harvest_api import HarvestApi
from .. import ui

timer = namespace("timer")


@timer.subcommand()
@decos.config_required
@decos.get_projects
def create(ctx: Context):
    """\
    Creates a timer
    Will also start the timer"""
    api: HarvestApi = ctx.api
    cache: utils.Cache = ctx.cache
    projects: list[helpers.Project] = ctx.projects

    project_idx, _ = utils.exist_or_exit(
        ui.menu([project.name for project in projects])
    )
    print()

    project = projects[project_idx]
    task_idx, _ = utils.exist_or_exit(ui.menu([task.name for task in project.tasks]))
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
@decos.config_required
def running(ctx: Context, big: bool, clock_only: bool, interval: int = 10):
    """\
    Displays the currently running timer

    Arguments:
    interval=VALUE Interval in seconds which to refresh data
                   by calling the API. Defaults to 10

    --big          Use larger clock characters
    --clock_only   Only display the clock
    """
    api: HarvestApi = ctx.api

    size = "big" if big else "small"
    message = ui.running_ui(api, interval, size, clock_only)
    if message is not None:
        print(message)


@timer.subcommand()
@decos.config_required
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
        if len(entries) == 0:
            print(f"{fg.RED}No Entries to Start{effects.CLEAR}")
            return

        entry_idx, _ = utils.pick_time_entry(entries)
        entry_id = entries[entry_idx].id
        cache["running_timer"] = entry_id
        cache.save()

    res = api.patch(f"/time_entries/{entry_id}/restart")
    utils.print_valid_response(res, "Timer Started!")


@timer.subcommand()
@decos.config_required
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
@decos.config_required
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
        if len(entries) == 0:
            print(f"{fg.RED}No Entries to Delete{effects.CLEAR}")
            return
        entry_idx, _ = utils.pick_time_entry(entries)
        entry_id = entries[entry_idx].id

    res = api.delete(f"/time_entries/{entry_id}")
    utils.print_valid_response(res, "Timer Deleted")
