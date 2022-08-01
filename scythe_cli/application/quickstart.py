import datetime as dt
import typing as t
import webbrowser
import oyaml as yaml  # type: ignore
from arc import Flag, errors, Context, command, Option

from scythe_cli import utils, constants
from scythe_cli.harvest_api import schemas


@command()
def quickstart(
    state: utils.ScytheState,
    ctx: Context,
    name: str,
    *,
    open_url: bool = Flag(short="o"),
    raw_duration: str = Option(name="duration", short="d", default="0"),
    notes: str = Option(default="", short="n"),
):
    """Launches an quickstart entry. One can be added with quickstart:add

    # Arguments
    name: Name of the quickstart entry
    open_url: Open the url of the quickstart enty in the browser, if one exists
    raw_duration: Create the timer with the specified duration, rather than starting it
    notes: Notes to add to the timer. Overrides the notes set in the config file
    """
    if raw_duration:
        duration = utils.parse_time(raw_duration)
    else:
        duration = 0

    if name not in state.config.quickstart:
        raise errors.ExecutionError(f"{name} not found in config")

    entry = state.config.quickstart[name]

    if not notes:
        notes = entry.notes or ""

    timer = state.harvest.time_entires.create(
        {
            "project_id": entry.project_id,
            "task_id": entry.task_id,
            "notes": notes,
            "spent_date": str(dt.date.today()),
            "hours": duration,
        }
    )

    state.harvest.time_entires.set_cached_running_timer(timer.dict())

    if duration:
        ctx.prompt.act(f"Timer created with a duration of {raw_duration}")
    else:
        ctx.prompt.ok("Timer started!")

    if open_url:
        if not entry.url:
            ctx.prompt.error("Task has no url, cannot launch browser")
        else:
            webbrowser.open_new_tab(entry.url)


@quickstart.subcommand(("list", "l"))
def list_entires(state: utils.ScytheState):
    """List all projects and tasks available to quickstart"""
    if not state.config.quickstart:
        print("No quickstart entries found in config")

    for name, data in state.config.quickstart.items():
        old_len = state.console.width
        state.console.width = 60 if old_len > 60 else old_len
        state.console.rule(name)
        state.console.print("Project ID:", data.project_id)
        state.console.print("Task ID:", data.task_id)
        state.console.print("Notes:", data.notes)
        state.console.print("URL:", data.url)
        state.console.width = old_len


@quickstart.subcommand(("add", "a"))
def add(state: utils.ScytheState, ctx: Context):
    """Add a quickstart entry"""

    name = ctx.prompt.input("Quickstart entry name: ", empty=False)

    assignments = state.harvest.project_assignments.list()
    project, p_idx = utils.select_project(assignments, ctx)
    task, _ = utils.select_task(assignments[p_idx].task_assignments, ctx)

    url = ctx.prompt.input("Url (optional): ")
    notes = ctx.prompt.input("Note (optional): ")

    config_dict = state.config.dict()
    config_dict["quickstart"][name] = {
        "project_id": project.id,
        "task_id": task.id,
        "url": url,
        "notes": notes,
    }

    with constants.CONFIG_FILE.open("w") as f:
        f.write(yaml.dump(config_dict))
