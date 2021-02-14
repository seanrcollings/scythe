from typing import Any
from collections import namedtuple

from arc import CLI, Context, namespace
from arc.color import effects, fg
from arc.errors import ExecutionError


from .. import cache_file, config_file, utils
from ..harvest_api import HarvestApi
from ..live_text import LiveText

from .projects import projects
from .stats import stats
from .timer import timer


Config = namedtuple("Config", ["token", "account_id", "user_id"])
cache = utils.Cache(cache_file)

context: dict[str, Any] = {}
if config_file.exists():
    # Any scripts that need access should use
    # the @utils.config_required decorator
    config = Config(**utils.load_file(config_file))
    context["config"] = config
    context["api"] = HarvestApi(config.token, config.account_id)

context["cache"] = cache


cli = CLI(context=context)
cli.install_commands(timer, projects, stats)


@cli.command()
def init(token: str, accid: int):
    """Used to write your Harvest
    ID and Access Token to the configuration file

    Arguments:
    token=TOKEN Harvest Account token generated at https://id.getharvest.com/developers
    accid=ID Harvest Account ID to be sent with every request
    """
    print("Checking a call can be made with the provided data...")
    init_api = HarvestApi(token, accid)
    res = init_api.me()

    if res.status_code != 200:
        raise ExecutionError(
            f"{fg.RED.bright}Error!{effects.CLEAR} The api returned a "
            f"{fg.YELLOW}{res.status_code}{effects.CLEAR} "
            f"with the following body:\n{res.text}"
        )

    file_config = {
        "TOKEN": token,
        "ACCOUNT_ID": accid,
        "USER_ID": res.json()["id"],
    }

    print(f"{fg.GREEN}Success!{effects.CLEAR}")
    print(
        "Creating config file with:",
        *(f"{key}: {value}" for key, value in file_config.items()),
        sep="\n",
    )
    with open(config_file, "w+") as file:
        file.write("\n".join(f"{key}={value}" for key, value in file_config.items()))

    print(f"{fg.GREEN}Config file written ({config_file}){effects.CLEAR}")


@cli.command()
@utils.config_required
def whoami(ctx: Context):
    """Prints out the user's info"""
    api: HarvestApi = ctx.api
    res: dict = api.me().json()
    line_length = len(max(res.keys(), key=len)) + 3
    transform = lambda string: " ".join(word.capitalize() for word in string.split("_"))
    for key, val in res.items():
        print(f"{transform(key):<{line_length}}: {val}")
