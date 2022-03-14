import datetime as dt
import os
import typing as t
import oyaml as yaml  # type: ignore
from arc import CLI, errors, Argument, Context, logging, present
from arc.color import fg, effects, colorize
import diskcache as dc  # type: ignore
from rich.table import Table
from rich.console import Console

from scythe_cli import utils
from scythe_cli.harvest_api import Harvest, RequestError
from .. import constants

from .timer import timer
from .quickstart import quickstart

cli = CLI(env=os.getenv("SCYTHE_ENV", "production"))  # type: ignore
cli.install_command(timer)
cli.install_command(quickstart)
cli.subcommand_aliases["t"] = "timer"
cli.subcommand_aliases["qs"] = "quickstart"


@cli.callback()
def setup(args, ctx: Context):
    if not constants.CONFIG_FILE.exists():
        raise errors.ExecutionError(
            f"No Config file present, run {colorize('scythe init', fg.YELLOW)}"
        )
    with constants.CONFIG_FILE.open() as f:
        ctx.state.config = utils.Config(**yaml.load(f, yaml.CLoader))

    cache = dc.Cache(constants.CACHE_DIR)
    ctx.state.cache = cache
    ctx.state.harvest = Harvest(
        ctx.state.config.token,
        ctx.state.config.account_id,
        cache,
        cache_for=ctx.state.config.cache_for,
    )

    ctx.state.logger = logging.getAppLogger("scy")
    ctx.state.console = Console(force_terminal=True)

    yield

    cache.close()


@setup.remove
@cli.command()
def init(
    token: str = Argument(prompt="Harvest Token: "),
    account_id: str = Argument(prompt="Harvest Account ID: "),
):
    """Sets up the config file

    # Arguments
    token: Harvest Account token generated at https://id.getharvest.com/developers
    account_id: Harvest Account ID to be sent with every request
    """
    print("Checking a call can be made with the provided data...")
    api = Harvest(
        token,
        account_id,
        dc.Cache(constants.CACHE_DIR),
    )
    try:
        user = api.me()
    except RequestError as e:
        raise errors.ExecutionError(
            f"{fg.BRIGHT_RED}Error!{effects.CLEAR} The api returned a "
            f"{fg.YELLOW}{e.status_code}{effects.CLEAR} "
            f"with the following body:\n{e.response.text}"
        )

    config = {
        "token": token,
        "account_id": account_id,
        "user_id": user.id,
        "quickstart": {},
    }

    print(f"{fg.GREEN}Success!{effects.CLEAR}")
    print(
        "Creating config file with:",
        *(f"{key}: {value}" for key, value in config.items()),
        sep="\n",
    )

    if not constants.CONFIG_DIR.exists():
        constants.CONFIG_DIR.mkdir()

    with constants.CONFIG_FILE.open("w+") as f:
        f.write(yaml.dump(config, Dumper=yaml.CDumper))

    print(f"{fg.GREEN}Config file written ({constants.CONFIG_FILE}){effects.CLEAR}")


@cli.command()
def whoami(state: utils.ScytheState):
    """Prints out info about the currently authenticated user"""
    user = state.harvest.me()

    for key, value in user.dict().items():
        print(f"{key}: {value}")


@cli.command(("projects", "p"))
def projects(state: utils.ScytheState):
    """Lists all projects and tasks that the current user is associated with"""

    assignments = state.harvest.project_assignments.list()
    for idx, assignment in enumerate(assignments):

        print(
            colorize(
                f"({idx}) {assignment.project.name}", effects.BOLD, constants.FG_ORANGE
            ),
            colorize(f"({assignment.project.id})", fg.GREY),
        )

        for task_idx, task_assignment in enumerate(assignment.task_assignments):
            print(
                f"\t({task_idx}) {task_assignment.task.name}",
                colorize(f"({task_assignment.task.id})", fg.GREY),
            )


@cli.command()
def clear_cache(state: utils.ScytheState):
    """Clears the data cache, guranteeting that subsequent requests will result in fresh data"""
    state.cache.clear()
    print("Cache Cleared")


@cli.command()
def stats(state: utils.ScytheState):
    delta = dt.timedelta(days=7)
    today = dt.date.today()
    timers = state.harvest.time_entires.list(
        {
            "from": today - delta,
            "to": today,
        }
    )

    hours = utils.fmt_time(
        *utils.get_hours_and_minutes(sum(timer.hours for timer in timers))
    )

    monday = today - dt.timedelta(days=today.weekday())
    week_timers = [timer for timer in timers if timer.spent_date >= monday]
    week_hours = utils.fmt_time(
        *utils.get_hours_and_minutes(sum(timer.hours for timer in week_timers))
    )

    yesterday = today - dt.timedelta(days=1)
    tomorrow = today + dt.timedelta(days=1)
    today_timers = [
        timer for timer in timers if tomorrow > timer.spent_date > yesterday
    ]
    today_hours = utils.fmt_time(
        *utils.get_hours_and_minutes(sum(timer.hours for timer in today_timers))
    )

    table = Table(title="Harvest Stats")
    table.add_column("Time Period")
    table.add_column("Number of Timers", justify="right", style="blue")
    table.add_column("Hours", justify="right")

    table.add_row("Last 7 Days", str(len(timers)), hours)
    table.add_row("Current Week", str(len(week_timers)), week_hours)
    table.add_row("Today", str(len(today_timers)), today_hours)

    state.console.print(table)
