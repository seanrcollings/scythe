import os
from collections import namedtuple
from typing import Any

from arc import CLI
from arc import Context, namespace
from arc.color import effects, fg
from arc.errors import ExecutionError

from .. import cache_file, config_file, decos, utils
from ..cache import Cache
from ..harvest_api import HarvestApi
from ..sync import Sync
from ..utils import ScytheContext
from .atomic import atomic
from .projects import projects
from .stats import stats
from .timer import timer

cli_context: dict[str, Any] = {}
cli_context["cache"] = Cache(cache_file)

if config_file.exists():
    # Any scripts that need access should use
    # the @decos.config_required decorator
    config = utils.Config.from_file(config_file)
    cli_context["config"] = config
    cli_context["api"] = HarvestApi(config.token, config.account_id)
    cli_context["syncer"] = Sync(
        cli_context["api"],
        cli_context["cache"],
        projects=lambda api: api.get_projects(config.user_id).json()[
            "project_assignments"
        ],
        running_timer=lambda api: api.get_running_timer(),
    )


cli = CLI(name="scythe", context=cli_context)
cli.install_commands(timer, projects, stats, atomic)


@cli.command()
def init(token: str, accid: int):
    """\
    Used to write your Harvest
    ID and Access Token to the configuration file

    # Arguments
    <TOKEN>  Harvest Account token generated at https://id.getharvest.com/developers
    <ID>     Harvest Account ID to be sent with every request
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
def whoami(ctx: ScytheContext):
    """Prints out the user's info"""
    res: dict = ctx.api.me().json()
    line_length = len(max(res.keys(), key=len)) + 3
    transform = lambda string: " ".join(word.capitalize() for word in string.split("_"))
    for key, val in res.items():
        print(f"{transform(key):<{line_length}}: {val}")


@cli.command("cache")
def cache_cmd(ctx: ScytheContext):
    """Displays the contents of the cache"""
    with open(ctx.cache.cache_file, "r") as file:
        print(file.read())
    print(ctx.cache.cache_file)


@cache_cmd.subcommand()
def clear(ctx: ScytheContext):
    """Clears the cache's content"""
    os.remove(ctx.cache.cache_file)
    print("Cache cleared")


@cache_cmd.subcommand()
def delete(key: str, ctx: ScytheContext):
    """\
    Delete an object from the cache

    scythe cache:delete running_timer
    will delete the id of the cached running timer
    """
    ctx.cache.load()
    del ctx.cache[key]
    print(f"{key} deleted from cache")


@cli.command()
def sync(ctx: ScytheContext):
    """Syncs all the cache contents with Harvest"""
    ctx.syncer.sync_all()


if __file__ == "__main__":
    cli()
