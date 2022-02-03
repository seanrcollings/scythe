import datetime as dt
import json
import sys
import time
import typing as t
import arc
from arc.color import colorize, effects, fg
from arc.present import Box
from arc import prompt

from scythe_cli import utils
from scythe_cli.clock.clock import clock
from scythe_cli.harvest_api import schemas
from scythe_cli.utils import ScytheState, exist_or_exit
from .. import constants
from ..cache import Cache
from ..harvest_api import Harvest


T = t.TypeVar("T")

SelectReturn = tuple[int, T]


def get_running_timer(cache: Cache, harvest: Harvest):
    with cache:
        timer: t.Optional[schemas.TimeEntry] = cache.get("running_timer")
        if timer:
            hours, minutes = timer.time()
            updated_at: t.Optional[dt.datetime] = cache.updated_at("running_timer")
            if updated_at:
                delta = dt.datetime.now() - updated_at
                hours += delta.seconds // 3600
                minutes += delta.seconds // 60
                if minutes >= 60:
                    hours += minutes // 60
                    minutes %= 60

            timer.hours = hours + minutes / 60
            cache.set("running_timer", timer, False)
        else:
            timer = harvest.time_entires.running()
            cache["running_timer"] = timer

        return timer, cache.updated_at("running_timer")


def select_timer(timers, ctx: arc.Context) -> SelectReturn[schemas.TimeEntry]:
    tab = "       "
    return exist_or_exit(  # type: ignore
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


@arc.command()
def timer(
    ctx: arc.Context,
    state: ScytheState,
    *,
    duration: t.Optional[float] = arc.Param(short="d", default=0.0),
):
    """Create and start a new timer

    # Arguments
    duration: Duration of the timer in hours. If given, the timer will be created, but not started.
    """
    with state.cache:
        assignments = t.cast(
            list[schemas.ProjectAssignment],
            state.cache.get("project_assignments")
            or state.harvest.project_assignments.list(),
        )
    projects = [a.project for a in assignments]
    print("Select a project:")
    p_idx, _ = t.cast(
        SelectReturn[str],
        utils.exist_or_exit(prompt.select([p.name for p in projects]), ctx),
    )
    print()

    project = projects[p_idx]

    tasks = [t.task for t in assignments[p_idx].task_assignments]
    print("Select a task:")
    t_idx, _ = t.cast(
        SelectReturn[str],
        utils.exist_or_exit(prompt.select([t.name for t in tasks]), ctx),
    )
    print()
    task = tasks[t_idx]

    note = ctx.prompt.input("Enter a note:", empty=False)

    timer = state.harvest.time_entires.create(
        {
            "project_id": project.id,
            "task_id": task.id,
            "notes": note,
            "spent_date": str(dt.date.today()),
            "hours": duration,
        }
    )

    if duration == 0:
        with state.cache as cache:
            cache["running_timer"] = timer

    ctx.prompt.ok("Timer created!")


@timer.subcommand()
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
        }
    )
    if len(timers) == 0:
        ctx.prompt.error("No timers found")
        return

    idx, _ = select_timer(timers, ctx)
    timer = timers[idx]

    state.harvest.time_entires.delete(timer.id)
    if timer.is_running:
        with state.cache:
            state.cache["running_timer"] = None

    ctx.prompt.ok("Timer deleted!")


@timer.subcommand()
def start(ctx: arc.Context, state: ScytheState):
    """Start a timer

    If a timer is currently running, it will be stopped. The currently running timer will be highlighted in orange.
    """
    timers = state.harvest.time_entires.list({"from": dt.date.today()})
    if len(timers) == 0:
        ctx.prompt.error("No timers found")
        return
    idx, _ = select_timer(timers, ctx)

    timer = timers[idx]
    if timer.is_running:
        ctx.prompt.no("Cannot restart an already running timer")
        ctx.exit(1)

    state.harvest.time_entires.restart(timer.id)
    with state.cache:
        state.cache["running_timer"] = timer
    ctx.prompt.ok("Timer started!")


@timer.subcommand()
def stop(ctx: arc.Context, state: ScytheState):
    """Stops a timer if one is currently running"""
    timer = state.harvest.time_entires.running()
    if not timer:
        ctx.prompt.no("No timer is currently running")
        ctx.exit(1)

    state.harvest.time_entires.stop(timer.id)
    ctx.prompt.ok("Timer stopped!")
    with state.cache as cache:
        cache["running_timer"] = None


@timer.subcommand()
def running(state: ScytheState, show_sync: bool = arc.Flag(short="s")):
    """Display the currently running timer

    # Arguments
    poll_duration: Polling interval in seconds. Defaults to 10
    """
    with state.cache as cache:
        cache["running_timer"] = state.harvest.time_entires.running()

    while True:
        timer, updated_at = get_running_timer(state.cache, state.harvest)
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

        print("\033c", end="")
        print(
            utils.Columns(
                constants.SCYTHE,
                str(pretty_clock),
            ),
            end="",
        )
        if show_sync:
            print(f'Sycned: {updated_at.strftime("%-I:%M %p")}')
        time.sleep(3)


@running.subcommand()
def waybar(state: utils.ScytheState, ctx: arc.Context):
    """Outputs a JSON encoded representation of
    the currently running timer to be used with
    waybar (https://github.com/Alexays/Waybar)
    """
    timer, updated_at = get_running_timer(state.cache, state.harvest)
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
            "tooltip": f"{timer.notes} ({updated_at.strftime('%-I:%M %p')})",
        }

    sys.stdout.write(json.dumps(output))
