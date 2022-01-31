import datetime
import time
import pydantic
import typing as t
import yaml
from arc import CLI, Param, State, callback, errors, Argument, Context
from arc.present import Box
from arc.color import fg, bg, effects, colorize
from arc import prompt

from scythe_cli import utils
from scythe_cli.cache import Cache
from scythe_cli.clock.clock import clock
from scythe_cli.harvest_apy import schemas

from scythe_cli.harvest_apy.api import Harvest, RequestError
from .. import globals


class Config(pydantic.BaseSettings):
    token: str
    account_id: str
    user_id: str
    extensions: t.Optional[dict] = None


class ScytheState(State):
    config: Config
    harvest: Harvest
    cache: Cache


cli = CLI(env="development")


@cli.callback
def setup(args, ctx: Context):
    if ctx.command != init:
        if not globals.CONFIG_FILE.exists():
            raise errors.ExecutionError(
                f"No Config file present, run {colorize('scythe init', fg.YELLOW)}"
            )
        with globals.CONFIG_FILE.open() as f:
            ctx.state.config = Config(**yaml.load(f, yaml.CLoader))

        ctx.state.harvest = Harvest(ctx.state.config.token, ctx.state.config.account_id)
        ctx.state.cache = ctx.resource(Cache(str(globals.CACHE_FILE)))

    yield


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
    api = Harvest(token, account_id)
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
    }

    print(f"{fg.GREEN}Success!{effects.CLEAR}")
    print(
        "Creating config file with:",
        *(f"{key}: {value}" for key, value in config.items()),
        sep="\n",
    )

    if not globals.CONFIG_DIR.exists():
        globals.CONFIG_DIR.mkdir()

    with globals.CONFIG_FILE.open("w+") as f:
        f.write(yaml.dump(config, Dumper=yaml.CDumper))

    print(f"{fg.GREEN}Config file written ({globals.CONFIG_FILE}){effects.CLEAR}")


@cli.command()
def whoami(state: ScytheState):
    user = state.harvest.me()

    for key, value in user.dict().items():
        print(f"{key}: {value}")


@cli.command()
def projects(state: ScytheState):
    assignments = state.harvest.project_assignments.list()
    for idx, assignment in enumerate(assignments):

        print(
            colorize(
                f"({idx}) {assignment.project.name}", effects.BOLD, globals.FG_ORANGE
            ),
            colorize(f"({assignment.id})", fg.GREY),
        )

        for task_idx, task_assignment in enumerate(assignment.task_assignments):
            print(f"\t({task_idx}) {task_assignment.task.name}")


@cli.command()
def sync(state: ScytheState):
    cache = state.cache
    cache["project_assignments"] = state.harvest.project_assignments.list()


T = t.TypeVar("T")

SelectReturn = tuple[int, T]


@cli.command()
def timer(
    ctx: Context,
    state: ScytheState,
    *,
    duration: t.Optional[float] = Param(short="d", default=0.0),
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
    while True:

        timer = state.harvest.time_entires.running()
        if not timer:
            print("No timer running")
            return

        content = f"""\
{clock(*timer.time())}
{colorize('PROJECT', globals.FG_ORANGE, effects.BOLD)}: {timer.project['name']}
{colorize('TASK', globals.FG_ORANGE, effects.BOLD)}: {timer.task['name']}
{colorize('NOTES', globals.FG_ORANGE, effects.BOLD)}: {timer.notes}
    """

        pretty_clock = Box(
            content,
            padding={"top": 3, "bottom": 3, "left": 3, "right": 1},
            justify="center",
        )

        print("\033c", end="")
        print(
            utils.Columns(
                globals.SCYTHE,
                str(pretty_clock),
            ),
            end="",
        )
        time.sleep(10)
