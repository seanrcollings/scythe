import datetime
import time
from collections import namedtuple

from arc import CLI, Utility
from arc.color import effects, fg
from arc.errors import ExecutionError
from arc.ui import SelectionMenu


from . import cache_file, config_file, helpers, utils
from .harvest_api import HarvestApi
from .live_text import LiveText

Config = namedtuple("Config", ["token", "account_id", "user_id"])
config = Config(**utils.load_file(config_file))
cache = utils.Cache(cache_file)


timer = Utility("timer")
projects = Utility("project")
stats = Utility("stats")
cli = CLI(utilities=[timer, projects, stats])

if config_file.exists():
    # Any scripts that need access should use
    # the @utils.config_required decorator
    api = HarvestApi(config.token, config.account_id)


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

    print(f"Config file written to ({config_file})")


@cli.script()
@utils.config_required
def whoami():
    """Prints out the user's info"""
    res: dict = api.me().json()
    line_length = len(max(res.keys(), key=len)) + 3
    transform = lambda string: " ".join(word.capitalize() for word in string.split("_"))
    for key, val in res.items():
        print(f"{transform(key):<{line_length}}: {val}")


@projects.script("list")
@utils.config_required
def list_projects():
    """Lists all of the user's projects and each project's tasks"""
    projects = api.get_projects(config.user_id).json()["project_assignments"]
    projects = helpers.Project.from_list(projects)

    for idx, project in enumerate(projects):
        print(f"{effects.BOLD}{fg.GREEN}({idx}) {project.name}{effects.CLEAR}")

        for task_idx, task in enumerate(project.tasks):
            print(f"\t({task_idx}) {task.name}")


@timer.script()
@utils.config_required
def create():
    """Creates a timer
    Starts the timer as well"""
    projects = api.get_projects(config.user_id).json()["project_assignments"]
    projects = helpers.Project.from_list(projects)

    project_idx, _ = utils.exist_or_exit(
        SelectionMenu([project.name for project in projects]).run()
    )
    print()

    project = projects[project_idx]

    task_idx, _ = utils.exist_or_exit(
        SelectionMenu([task.name for task in project.tasks]).run()
    )
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
def running(interval: int = 10):
    """Displays the currently running timer

    interval=VALUE interval in which to refresh data by calling the api. Defaults
        to 10
    """
    entry = api.get_running_timer()
    if not entry:
        print("No running timer")
        return

    entry = helpers.TimeEntry(entry)
    hours, minutes = utils.parse_time(entry.hours)
    format_str = (
        "Time Spent: {hours} \n Project: {project_name}\n"
        " Task: {task_name}\n Notes: {notes}"
    )
    text = LiveText(
        format_str.format(
            hours=f"{hours}:{minutes}",
            project_name=entry.project["name"],
            task_name=entry.task["name"],
            notes=entry.notes,
        )
    )

    while True:
        entry = api.get_running_timer()
        if not entry:
            print("Timer stopped running")
            return

        entry = helpers.TimeEntry(entry)
        hours, minutes = utils.parse_time(entry.hours)

        text.update(
            format_str.format(
                hours=utils.format_time(hours, minutes),
                project_name=entry.project["name"],
                task_name=entry.task["name"],
                notes=entry.notes,
            )
        )

        time.sleep(interval)


@timer.script()
@timer.script("restart")
@utils.config_required
def start(cached: bool):
    """Start a previously created timer.

    Arguments:
    --cached   Will check the cache for an ENTRY_ID and start that timer
    """

    entry_id = None
    if cached:
        entry_id = cache.read("entry_id")

    if not entry_id:
        print("Fetching timers from today...")
        entries = api.get(f"/time_entries?from={datetime.date.today()}").json()[
            "time_entries"
        ]
        entries = helpers.TimeEntry.from_list(entries)
        entry_idx, _ = utils.pick_time_entry(entries)
        entry_id = entries[entry_idx].id
        cache.write(entry_id=entry_id)

    res = api.patch(f"/time_entries/{entry_id}/restart")
    utils.print_valid_response(res, "Timer Started!")


@timer.script()
@utils.config_required
def stop(cached: bool):
    """Stops a running timer.

    Arguments:
    --cached  Will check the cache for an ENTRY_ID and stop that timer
    """

    entry_id = None
    if cached:
        entry_id = cache.read("entry_id")

    if not entry_id:
        print("Checking Harvest for running timers...")
        entry = api.get_running_timer()
        if not entry:
            print("No running timers")
            return

        entry_id = entry["id"]

    res = api.patch(
        f"/time_entries/{entry_id}/stop",
    )
    utils.print_valid_response(res, "Timer Stopped!")
    cache.write(entry_id=entry_id)


@timer.script()
@utils.config_required
def delete(cached: bool):
    """Used to delete a timer from the current day's list
    Arguments:
    --cached  Will check the cache for an ENTRY_ID and delete that timer
    """

    entry_id = None
    if cached:
        entry_id = cache.read("entry_id")

    if not entry_id:
        payload = {"from": str(datetime.date.today())}
        print("Fetching timers from today...")
        entries = api.get("/time_entries", params=payload).json()["time_entries"]

        entries = helpers.TimeEntry.from_list(entries)
        entry_idx, _ = utils.pick_time_entry(entries)
        entry_id = entries[entry_idx].id

    res = api.delete(f"/time_entries/{entry_id}")
    utils.print_valid_response(res, "Timer Deleted")


@stats.script()
@utils.config_required
def today():
    """Prints out stats for today's projects"""
