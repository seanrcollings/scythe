import pydantic
import typing as t
import yaml
from arc import CLI, State, callback, errors, Argument
from arc.color import fg, bg, effects, colorize

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


@callback.create
def setup(args, ctx):
    if not globals.CONFIG_FILE.exists():
        raise errors.ExecutionError(
            f"No Config file present, run {colorize('scythe init', fg.YELLOW)}"
        )
    with globals.CONFIG_FILE.open() as f:
        ctx.state.config = Config(**yaml.load(f, yaml.CLoader))

    ctx.state.harvest = Harvest(ctx.state.config.token, ctx.state.config.account_id)

    yield


cli = CLI(env="development")


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


@setup
@cli.command()
def whoami(state: ScytheState):
    user = state.harvest.me()

    for key, value in user.dict().items():
        print(f"{key}: {value}")


@setup
@cli.command()
def projects(state: ScytheState):
    ...