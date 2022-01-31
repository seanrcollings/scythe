import datetime
import time
import typing as t
import arc
from arc.color import colorize, effects
from arc.present import Box
from arc import prompt

from scythe_cli import utils
from scythe_cli.clock.clock import clock
from scythe_cli.harvest_api import schemas
from scythe_cli.utils import ScytheState
from .. import constants


T = t.TypeVar("T")

SelectReturn = tuple[int, T]


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

    state.harvest.time_entires.create(
        {
            "project_id": project.id,
            "task_id": task.id,
            "notes": note,
            "spent_date": str(datetime.date.today()),
            "hours": duration,
        }
    )

    ctx.prompt.ok("Timer created!")


@timer.subcommand()
def start():
    ...


@timer.subcommand()
def running(state: ScytheState):
    breakpoint()
    while True:

        timer = state.harvest.time_entires.running()
        if not timer:
            print("No timer running")
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
        time.sleep(10)