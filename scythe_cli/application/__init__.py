import datetime as dt
import os
import typing as t
import oyaml as yaml  # type: ignore
import arc
from arc import Context
from arc.color import fg, effects, colorize
from arc.logging import logger
import diskcache as dc  # type: ignore
from rich.table import Table
from rich.console import Console
from rich.tree import Tree

from scythe_cli import utils
from scythe_cli.harvest_api import Harvest, RequestError
from .. import constants

from .timer import timer
from .quickstart import quickstart


@arc.decorator()
def setup(ctx: Context):
    if not constants.CONFIG_FILE.exists():
        raise arc.ExecutionError(
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

    ctx.state.logger = logger
    ctx.state.console = Console(force_terminal=True)
    ctx.resource(cache)


arc.configure(environment=os.getenv("SCYTHE_ENV", "production"))
cli = arc.namespace(name="scythe")
cli.decorators.add(setup)

cli.add_command(timer, ["t"])
cli.add_command(quickstart, ["qs"])
cli.autoload(constants.AUTOLOAD_DIR)


@setup.remove
@cli.subcommand()
def init(
    token: str = arc.Argument(prompt="Harvest Token: "),
    account_id: str = arc.Argument(prompt="Harvest Account ID: "),
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
        raise arc.ExecutionError(
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


@cli.subcommand()
def whoami(state: utils.ScytheState):
    """Prints out info about the currently authenticated user"""
    user = state.harvest.me()

    for key, value in user.dict().items():
        state.console.print(f"{key}: {value}")


@cli.subcommand(("projects", "p"))
def projects(state: utils.ScytheState):
    """Lists all projects and tasks that the current user is associated with"""

    assignments = state.harvest.project_assignments.list()
    tree = Tree("Harvest Projects")
    for assignment in assignments:

        sub = tree.add(f"[blue]{assignment.project.name}[/]")

        for task_assignment in assignment.task_assignments:
            sub.add(f"{task_assignment.task.name}")

    state.console.print(tree)


@cli.subcommand()
def clear_cache(state: utils.ScytheState):
    """Clears the data cache, guranteeting that subsequent requests will result in fresh data"""
    state.cache.clear()
    print("Cache Cleared")


@cli.subcommand()
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
