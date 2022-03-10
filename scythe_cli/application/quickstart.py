import datetime as dt
import typing as t
import webbrowser
import oyaml as yaml  # type: ignore
from arc import Flag, errors, Argument, Context, Param, command
from arc.color import fg, effects, colorize

from scythe_cli import utils, constants
from scythe_cli.harvest_api import schemas


@command()
def quickstart(
    state: utils.ScytheState,
    ctx: Context,
    project_name: str = Argument(name="project"),
    task_name: str = Argument(name="task"),
    *,
    open_url: bool = Flag(short="o"),
    raw_duration: str = Param(name="duration", short="d", default="0"),
    notes: str = Param(default="", short="n"),
):
    """Launches an quickstart entry. One can be added with quickstart:add

    # Arguments
    project_name: Name of the project to create a timer for
    task_name: Name of the task to create a timer for
    open_url: Open the url of the timer in the browser, if one exists
    raw_duration: Create the timer with the specified duration, rather than starting it
    notes: Notes to add to the timer. Overrides the notes set in the config file1
    """
    if raw_duration:
        duration = utils.parse_time(raw_duration)
    else:
        duration = 0

    if project_name not in state.config.quickstart:
        raise errors.ExecutionError(f"Project {project_name} not found in config")

    project = state.config.quickstart[project_name]

    if task_name not in project.tasks:
        raise errors.ExecutionError(
            f"Task {task_name} not found in project {project_name}"
        )

    task = project.tasks[task_name]

    if not notes and not isinstance(task, int):
        notes = task.notes or ""

    timer = state.harvest.time_entires.create(
        {
            "project_id": project.id,
            "task_id": task if isinstance(task, int) else task.id,
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
        if isinstance(task, int) or task.url is None:
            ctx.prompt.error("Task has no url, cannot launch browser")
        else:
            webbrowser.open_new_tab(task.url)


@quickstart.subcommand(("list", "l"))
def list_entires(state: utils.ScytheState):
    """List all projects and tasks available to quickstart"""
    if not state.config.quickstart:
        print("No quickstart entries found in config")

    for idx, (name, data) in enumerate(state.config.quickstart.items()):
        print(
            colorize(f"({idx}) {name}", effects.BOLD, constants.FG_ORANGE),
            colorize(f"({data.id})", fg.GREY),
        )

        for task_idx, (task_name, task_data) in enumerate(data.tasks.items()):
            print(f"   ({task_idx}) {colorize(task_name, effects.BOLD)}")
            if isinstance(task_data, int):
                print(f"   \uff5c id: {task_data}")
            else:
                for key, value in task_data.dict().items():
                    if value:
                        print(f"    \u2502 {key}: {value}")


# TODO:
# - Select from currently-existing projects first
# - Handling overwiting of project aliases?
# - Handling overwiting of task aliases?


@quickstart.subcommand(("add", "a"))
def add(state: utils.ScytheState, ctx: Context):
    """Add a quickstart entry. Work in progress"""

    assignments = state.harvest.project_assignments.list()

    project, p_idx = utils.select_project(assignments, ctx)
    project_alias = ctx.prompt.input("Project alias (optional): ") or project.name
    task, _ = utils.select_task(assignments[p_idx].task_assignments, ctx)
    task_alias = ctx.prompt.input("Task alias (optional): ") or task.name

    url = ctx.prompt.input("Url (optional): ")
    notes = ctx.prompt.input("Note (optional): ")

    config_dict = state.config.dict()
    current_tasks: dict = (
        config_dict["quickstart"].get(project_alias, {}).get("tasks", {})
    )

    if any((url, notes)):
        value: t.Any = {"id": task.id, "url": url, "notes": notes}
    else:
        value = task.id

    config_dict["quickstart"][project_alias] = {
        "id": project.id,
        "tasks": current_tasks | {task_alias: value},
    }

    with constants.CONFIG_FILE.open("w") as f:
        f.write(yaml.dump(config_dict))
