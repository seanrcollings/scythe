from typing import Any
from collections import namedtuple
import os

from arc import CLI, Context, namespace, CommandType as ct
from arc.color import effects, fg
from arc.errors import ExecutionError

from .. import cache_file, config_file, utils
from .. import decos
from ..harvest_api import HarvestApi
from .projects import projects
from .stats import stats
from .timer import timer
from .atomic import atomic


cli_context: dict[str, Any] = {}
if config_file.exists():
    # Any scripts that need access should use
    # the @decos.config_required decorator
    config = utils.Config.from_file(config_file)
    cli_context["config"] = config
    cli_context["api"] = HarvestApi(config.token, config.account_id)

cli_context["cache"] = utils.Cache(cache_file)


cli = CLI(context=cli_context)
cli.install_commands(timer, projects, stats, atomic)


@cli.command()
def init(token: str, accid: int):
    """\
    Used to write your Harvest
    ID and Access Token to the configuration file

    Arguments:
    token=TOKEN  Harvest Account token generated
                 at https://id.getharvest.com/developers
    accid=ID     Harvest Account ID to be
                 sent with every request
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

    config_map = {
        "TOKEN": token,
        "ACCOUNT_ID": accid,
        "USER_ID": res.json()["id"],
    }

    print(f"{fg.GREEN}Success!{effects.CLEAR}")
    print(
        "Creating config file with:",
        *(f"{key}: {value}" for key, value in config_map.items()),
        sep="\n",
    )
    with open(config_file, "w+") as file:
        file.write("\n".join(f"{key}={value}" for key, value in config_map.items()))

    print(f"{fg.GREEN}Config file written ({config_file}){effects.CLEAR}")


@cli.command()
@decos.config_required
def whoami(ctx: Context):
    """Prints out the user's info"""
    api: HarvestApi = ctx.api
    res: dict = api.me().json()
    line_length = len(max(res.keys(), key=len)) + 3
    transform = lambda string: " ".join(word.capitalize() for word in string.split("_"))
    for key, val in res.items():
        print(f"{transform(key):<{line_length}}: {val}")


@cli.command("cache")
def cache_cmd(ctx: Context):
    """Displays the contents of the cache"""
    cache: utils.Cache = ctx.cache
    with open(cache.cache_file, "r") as file:
        print(file.read())
    print(cache.cache_file)


@cache_cmd.subcommand()
def clear(ctx: Context):
    """Clears the cache's content"""
    cache: utils.Cache = ctx.cache
    os.remove(cache.cache_file)
    print("Cache cleared")


@cache_cmd.subcommand(command_type=ct.POSITIONAL)
def delete(key: str, ctx: Context):
    """\
    Delete an object from the cache

    scythe cache:delete running_timer
    will delete the id of the cached running timer
    """
    cache: utils.Cache = ctx.cache
    cache.load()
    del cache[key]
    print(f"{key} deleted from cache")


if __file__ == "__main__":
    cli()
