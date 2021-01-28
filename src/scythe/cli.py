import datetime
import re

from arc import CLI, Utility
from arc.errors import ExecutionError
from arc.color import fg, effects
from arc.utilities.debug import debug

from . import config_file, cache_file
from .harvest_api import HarvestApi
from . import utils
from .selection_menu import SelectionMenu
from .helpers.project import Project


config = utils.load_file(config_file)
cache = utils.Cache(cache_file)


timer = Utility("timer")
cli = CLI(utilities=[debug, timer])

if config_file.exists():
    # Any scripts that need access should use
    # the @utils.config_required decorator
    api = HarvestApi(config["token"], config["account_id"])


@cli.script()
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
            f"{fg.YELLOW}{res.status_code}{effects.CLEAR} with the following body:\n{res.text}"
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

    print(f"Config file written to ({config_file})")


@timer.script("list")
@utils.config_required
def list_projects():
    projects = api.get_projects(config["user_id"]).json()["project_assignments"]
    projects = Project.from_list(projects)

    for idx, project in enumerate(projects):
        print(f"{effects.BOLD}{fg.GREEN}({idx}) {project.name}{effects.CLEAR}")

        for task_idx, task in enumerate(project.tasks):
            print(f"\t({task_idx}) {task.name}")


@timer.script()
@utils.config_required
def start():
    projects = api.get_projects(config["user_id"]).json()["project_assignments"]
    projects = Project.from_list(projects)

    project_idx, _ = SelectionMenu([project.name for project in projects]).render()
    print()

    project = projects[project_idx]

    task_idx, _ = SelectionMenu([task.name for task in project.tasks]).render()
    print()

    task = project.tasks[task_idx]

    print(f"{effects.BOLD}Project{effects.CLEAR}: {project.name}")
    print(f"{effects.BOLD}Task{effects.CLEAR}: {task.name}")

    note = input("Note: ")

    res = api.post(
        "/time_entries",
        {
            "project_id": project.id,
            "task_id": task.id,
            "spent_date": str(datetime.date.today()),
            "notes": note,
        },
    )

    utils.print_valid_response(res, "Timer Started!")
    cache.write(entry_id=res.json()["id"])


@timer.script()
@utils.config_required
def stop():
    entry_id = cache.read("entry_id")

    if not entry_id:
        print("Missed cache... Checking for running timers")
        entry = api.get_running_timer()
        if not entry:
            print("No running timers")
            return

        entry_id = entry["id"]

    api.patch(
        f"/time_entries/{entry_id}/stop",
    )
    print("Timer Stopped!")
