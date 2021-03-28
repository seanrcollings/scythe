import datetime
from typing import cast
from arc import namespace
from arc.color import effects, fg

from .. import helpers
from .. import utils
from .. import decos
from .. import ui
from .running import running

timer = namespace("timer")
timer.install_command(running)


@timer.subcommand()
@decos.config_required
@decos.get_projects
def create(ctx: utils.ScytheContext):
    """\
    Creates a timer
    Will also start the timer"""
    projects = cast(list[helpers.Project], ctx.projects)

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

    res = ctx.api.create_timer(project_id=project.id, task_id=task.id, notes=note)

    utils.print_valid_response(res, "Timer Started!")
    ctx.cache["running_timer"] = res.json()
    ctx.cache.save()


@timer.subcommand()
@decos.config_required
def start(last: bool, ctx: utils.ScytheContext):
    """Start a previously created timer.

    Arguments:
    --last   will start the last stopped timer
    """

    entry_id = None
    if last:
        entry_id = ctx.cache["last_running_timer"].get("id")

    if not entry_id:
        print("Fetching timers from today...")
        entries = ctx.api.get(f"/time_entries?from={datetime.date.today()}").json()[
            "time_entries"
        ]
        entries = helpers.Timer.from_list(entries)
        if len(entries) == 0:
            print(f"{fg.RED}No Entries to Start{effects.CLEAR}")
            return

        entry_idx, _ = utils.pick_time_entry(entries)
        entry_id = entries[entry_idx].id
        ctx.cache["running_timer"] = entries[entry_idx].data
        ctx.cache.save()

    res = ctx.api.patch(f"/time_entries/{entry_id}/restart")
    utils.print_valid_response(res, "Timer Started!")


@timer.subcommand()
@decos.config_required
def stop(cached: bool, ctx: utils.ScytheContext):
    """Stops a running timer.

    Arguments:
    --cached  Will check the cache
              for an running_timer and stop that timer
    """

    entry_id = None
    if cached:
        entry_id = ctx.cache["running_timer"].get("id")

    if not entry_id:
        print("Checking Harvest for running timers...")
        entry = ctx.api.get_running_timer()
        if not entry:
            print("No running timers")
            return

        entry_id = entry["id"]

    res = ctx.api.patch(
        f"/time_entries/{entry_id}/stop",
    )
    utils.print_valid_response(res, "Timer Stopped!")
    ctx.cache["last_running_timer"] = ctx.cache.pop("running_timer")
    if ctx.cache["updated_at"]:
        ctx.cache.pop("updated_at")
    ctx.cache.save()


@timer.subcommand()
@decos.config_required
def delete(cached: bool, ctx: utils.ScytheContext):
    """Used to delete a timer from the current day's list

    Arguments:
    --cached  Will check the cache
              for an running_timer and delete that timer
    """

    entry_id = None
    if cached:
        entry_id = ctx.cache["running_timer"].get("id")

    if not entry_id:
        payload = {"from": str(datetime.date.today())}
        print("Fetching timers from today...")
        entries = ctx.api.get("/time_entries", params=payload).json()["time_entries"]

        entries = helpers.Timer.from_list(entries)
        if len(entries) == 0:
            print(f"{fg.RED}No Entries to Delete{effects.CLEAR}")
            return
        entry_idx, _ = utils.pick_time_entry(entries)
        entry_id = entries[entry_idx].id

    res = ctx.api.delete(f"/time_entries/{entry_id}")
    ctx.cache.pop("running_timer")
    ctx.cache.save()
    utils.print_valid_response(res, "Timer Deleted")
