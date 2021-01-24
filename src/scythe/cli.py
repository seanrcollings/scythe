import datetime
import re

from arc import CLI, Utility
from arc.errors import ExecutionError
from arc.color import fg, effects
from arc.utilities.debug import debug

from . import config_file, cache_file
from .harvest_api import HarvestApi
from . import utils


config = utils.load_file(config_file)
cache = utils.Cache(cache_file)


timer = Utility("timer")
cli = CLI(utilities=[debug, timer])


@cli.script()
def init(token: str, accid: int):
    """Used to write your Harvest
    ID and Access Token to the configuration file
    params:
    token=TOKEN Harvest Account token generated at https://id.getharvest.com/developers
    accid=ID Harvest Account ID to be sent with every request
    """
    print("Checking a call can be made with the provided data...")
    api = HarvestApi(token, accid)
    res = api.me()
    # use the result to also store the user id :)
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
    api = HarvestApi(config["token"], config["account_id"])
    assignments = api.get(f"/users/{config['user_id']}/project_assignments").json()[
        "project_assignments"
    ]

    utils.print_assignments(assignments, show_tasks=True)


@timer.script()
@utils.config_required
def start():
    api = HarvestApi(config["token"], config["account_id"])
    assignments = api.get(f"/users/{config['user_id']}/project_assignments").json()[
        "project_assignments"
    ]

    utils.print_assignments(assignments, show_tasks=True)
    validated_input = None
    while not validated_input:
        print(
            effects.UNDERLINE,
            "Select the project and task to start a timer (i.e. 1, 1)",
            effects.CLEAR,
            sep="",
        )
        user_input = input(">>> ")
        # regex match input here
        # Try catch block here
        validated_input = tuple(int(value) for value in user_input.split(","))

    project_idx, task_idx = validated_input

    print(f"Project: {assignments[project_idx]['project']['name']}")
    print(
        f"Task: {assignments[project_idx]['task_assignments'][task_idx]['task']['name']}"
    )

    note = input("Note: ")

    res = api.post(
        "/time_entries",
        {
            "project_id": assignments[project_idx]["project"]["id"],
            "task_id": assignments[project_idx]["task_assignments"][task_idx]["task"][
                "id"
            ],
            "spent_date": str(datetime.date.today()),
            "notes": note,
        },
    )

    utils.handle_response(res, "Timer Started!")
    cache.write(entry_id=res.json()["id"])


@timer.script()
@utils.config_required
def stop():
    entry_id = cache.read("entry_id")

    api = HarvestApi(config["token"], config["account_id"])
    api.patch(
        f"/time_entries/{entry_id}/stop",
    )
    print("Timer Stopped")
