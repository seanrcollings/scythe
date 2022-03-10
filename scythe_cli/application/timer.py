import datetime as dt
import enum
import json
import sys
import time
import typing as t
import arc
from arc.color import colorize, effects, fg
from arc.present import Box
from arc import prompt, errors

from scythe_cli import utils
from scythe_cli.clock.clock import clock
from scythe_cli.harvest_api import schemas
from scythe_cli.utils import ScytheState, exist_or_exit
from .. import constants
from ..cache import Cache
from ..harvest_api import Harvest


T = t.TypeVar("T")


# def get_running_timer(cache: Cache, harvest: Harvest):
#     with cache:
#         timer: t.Optional[schemas.TimeEntry] = cache.get("running_timer")
#         if timer:
#             hours, minutes = timer.time()
#             updated_at: t.Optional[dt.datetime] = cache.updated_at("running_timer")
#             if updated_at:
#                 delta = dt.datetime.now() - updated_at
#                 hours += delta.seconds // 3600
#                 minutes += delta.seconds // 60
#                 if minutes >= 60:
#                     hours += minutes // 60
#                     minutes %= 60

#             timer.hours = hours + minutes / 60
#             cache.set("running_timer", timer, False)
#         else:
#             timer = harvest.time_entires.running()
#             cache["running_timer"] = timer

#         return timer, cache.updated_at("running_timer")


def select_timer(timers, ctx: arc.Context) -> schemas.TimeEntry:
    tab = "       "
    idx, _ = exist_or_exit(  # type: ignore
        prompt.select(
            [
                (
                    colorize(f"({timer.fmt_time()})", effects.BOLD)
                    + f' {constants.FG_ORANGE if timer.is_running else ""}{effects.BOLD}'
                    f'{timer.project["name"]}{effects.CLEAR}\n'
                    f'{tab}{timer.task["name"]}\n'
                    f"{tab}{colorize(timer.notes or '', effects.ITALIC, fg.GREY)}\n"
                )
                for timer in timers
            ]
        ),
        ctx,
    )

    return timers[idx]


@arc.command("timer")
def timer(
    ctx: arc.Context,
    state: ScytheState,
    *,
    raw_duration: t.Optional[str] = arc.Param(name="duration", short="d", default="0"),
    allow_empty_notes: bool = arc.Param(short="e"),
):
    """Create and start a new timer

    # Arguments
    raw_duration: Duration of the timer in hours. If given, the timer will be created, but not started.
    allow_empty_notes: Allow empty notes.

    # Acceptable formats
    Acceptable formats for duration are:

    \b
    - Integer (1, 2, 3, 4, 5)
    - Decimal (1.5, 2.5, 3.5, 4.5, 5.5)
    - Hour:Minute (1:30, 2:30, 3:00, 4:30, 5:30)
    """
    if raw_duration:
        duration = utils.parse_time(raw_duration)
    else:
        duration = 0

    assignments = state.harvest.project_assignments.list()

    project, p_idx = utils.select_project(assignments, ctx)
    task, _ = utils.select_task(assignments[p_idx].task_assignments, ctx)

    note = ctx.prompt.input("Enter a note:", empty=allow_empty_notes)

    timer = state.harvest.time_entires.create(
        {
            "project_id": project.id,
            "task_id": task.id,
            "notes": note,
            "spent_date": str(dt.date.today()),
            "hours": duration,
        }
    )

    ctx.prompt.ok("Timer created!")

    if duration == 0:
        ctx.prompt.subtle("Timer has been started.")
        state.harvest.time_entires.set_cached_running_timer(timer.dict())


@timer.subcommand(("delete", "d"))
def delete(
    state: ScytheState, ctx: arc.Context, day: int = arc.Option(short="d", default=0)
):
    """Delete a timer

    # Arguments
    day: Days in the past, relative to today, to delete timers from. 1 is yesterday, 2 is 2 days ago, etc.
    """
    delta = dt.timedelta(days=day)

    timers = state.harvest.time_entires.list(
        {
            "from": dt.date.today() - delta,
            "to": dt.date.today() - delta,
        },
        use_cache=False,
    )
    if len(timers) == 0:
        ctx.prompt.error("No timers found for this day")
        return

    timer = select_timer(timers, ctx)

    state.harvest.time_entires.delete(timer.id)

    ctx.prompt.ok("Timer deleted!")


@timer.subcommand(("start", "s"))
def start(ctx: arc.Context, state: ScytheState):
    """Start a timer

    If a timer is currently running, it will be stopped. The currently running timer will be highlighted in orange.
    """
    timers = state.harvest.time_entires.list({"from": dt.date.today()}, use_cache=False)
    if len(timers) == 0:
        ctx.prompt.error("No timers found")
        return

    timer = select_timer(timers, ctx)

    if timer.is_running:
        ctx.prompt.no("Cannot restart an already running timer")
        ctx.exit(1)

    state.harvest.time_entires.restart(timer.id)
    ctx.prompt.ok("Timer started!")


@timer.subcommand(("stop", "f"))
def stop(ctx: arc.Context, state: ScytheState):
    """Stops a timer if one is currently running"""
    timer = state.harvest.time_entires.running()
    if not timer:
        ctx.prompt.no("No timer is currently running")
        ctx.exit(1)

    state.harvest.time_entires.stop(timer.id)
    ctx.prompt.ok("Timer stopped!")


class EditOptions(enum.IntEnum):
    """Options for the edit command"""

    DURATION = 0
    NOTE = 1
    PROJECT = 2
    TASK = 3
    CANCEL = 4
    SAVE = 5


@timer.subcommand(("edit", "e"))
def edit(
    ctx: arc.Context, state: ScytheState, day: int = arc.Option(short="d", default=0)
):
    """Edit a timer

    # Arguments
    day: Days in the past, relative to today, to delete timers from. 1 is yesterday, 2 is 2 days ago, etc.
    """

    delta = dt.timedelta(days=day)
    timers = state.harvest.time_entires.list(
        {
            "from": dt.date.today() - delta,
            "to": dt.date.today() - delta,
        }
    )
    if len(timers) == 0:
        ctx.prompt.error("No timers found for this day")
        return

    timer = select_timer(timers, ctx)
    params: dict[str, t.Any] = {}

    while True:
        try:
            ctx.prompt.act("What would you like to change?")
            idx, _ = utils.exist_or_exit(
                prompt.select(
                    [
                        f"Edit duration {colorize('(' + timer.fmt_time() + ')', constants.FG_ORANGE if timer.is_running else fg.GREY)}",
                        f"Edit note {colorize('(' + str(timer.notes) + ')', fg.GREY)}",
                        f"Edit project {colorize('(' + timer.project['name'] + ')', fg.GREY)}",
                        f"Edit task {colorize('(' + timer.task['name'] + ')', fg.GREY)}",
                        f"Cancel",
                        f"Save changes",
                    ],
                ),
                ctx,
            )

            if idx == EditOptions.DURATION:
                hours = utils.parse_time(
                    ctx.prompt.input("Enter a duration:", empty=False)
                )
                timer.hours = hours
                params["hours"] = hours

            elif idx == EditOptions.NOTE:
                note = ctx.prompt.input("Note:", empty=False)
                timer.notes = note
                params["notes"] = note

            elif idx == EditOptions.PROJECT:
                assignments = state.harvest.project_assignments.list()
                project, p_idx = utils.select_project(assignments, ctx)

                task, _ = utils.select_task(assignments[p_idx].task_assignments, ctx)

                timer.project = project.dict()
                timer.task = task.dict()
                params["project_id"] = project.id
                params["task_id"] = task.id

            elif idx == EditOptions.TASK:
                assignments = state.harvest.project_assignments.list()
                idx = 0
                for assn in assignments:
                    if assn.project.id == timer.project["id"]:
                        break

                    idx += 1

                task, _ = utils.select_task(assignments[idx].task_assignments, ctx)
                timer.task = task.dict()
                params["task_id"] = task.id

            elif idx == EditOptions.CANCEL:
                break

            elif idx == EditOptions.SAVE:
                state.harvest.time_entires.update(timer.id, params)
                if timer.is_running:
                    state.harvest.time_entires.set_cached_running_timer(timer.dict())
                ctx.prompt.ok("Timer updated!")
                break

        except Exception as e:
            if isinstance(e, errors.Exit):
                raise
            ctx.prompt.error(str(e))


@timer.subcommand(("running", "r"))
def running(
    state: ScytheState,
    exit: bool = arc.Flag(short="e"),
):
    """Display the currently running timer

    # Arguments
    exit: output the information once, then exit
    """

    while True:
        timer = state.harvest.time_entires.running()
        if not timer:
            print("No timers running")
            return

        content = f"""\
{clock(*timer.time())}
{colorize('PROJECT', constants.FG_ORANGE, effects.BOLD)}: {timer.project['name']}
{colorize('TASK', constants.FG_ORANGE, effects.BOLD)}: {timer.task['name']}
{colorize('NOTES', constants.FG_ORANGE, effects.BOLD)}: {timer.notes}
    """

        pretty_clock = Box(
            content,
            padding={"top": 3, "bottom": 3, "left": 3, "right": 1},
            justify="center",
        )

        if not exit:
            print("\033c", end="")

        print(
            utils.Columns(
                constants.SCYTHE,
                str(pretty_clock),
            ),
            end="",
        )

        if exit:
            return

        time.sleep(3)


@running.subcommand()
def waybar(state: utils.ScytheState, ctx: arc.Context):
    """Outputs a JSON encoded representation of
    the currently running timer to be used with
    waybar (https://github.com/Alexays/Waybar)
    """
    timer = state.harvest.time_entires.running()
    if not timer:
        output = {
            "text": "",
            "alt": "inactive",
            "class": "inactive",
            "tooltip": "No Timer Currently Running",
        }
    else:
        output = {
            "text": timer.fmt_time(),
            "alt": "active",
            "class": "active",
            "tooltip": f"{timer.notes}",
        }

    sys.stdout.write(json.dumps(output))
