import datetime
import subprocess
import typing as t
import arc
import msgspec
from arc.prompt import Prompt

from scythe_cli import constants
from scythe_cli.application import utils
from scythe_cli.application.console import console


class QuickStartEntry(msgspec.Struct):
    project: int
    task: int
    notes: t.Optional[str] = None
    exec: t.Optional[str] = None


@arc.command
def quickstart(prompt: Prompt, name: str, no_exec: bool = arc.Flag(short="n")):
    with constants.QUICKSTART_DATA.open() as f:
        config = msgspec.json.decode(f.read(), type=dict[str, QuickStartEntry])

    if name not in config:
        console.print(f"No entry with name: {name}")
        arc.exit(1)

    template = config[name]

    template.notes = (
        prompt.input("Notes: ") if template.notes is None else template.notes
    )

    with utils.get_harvest() as harvest:
        with console.status("Creating Timer..."):
            harvest.create_timer(
                {
                    "project_id": template.project,
                    "task_id": template.task,
                    "notes": template.notes,
                    "spent_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                }
            )

    if template.exec and not no_exec:
        console.print(f"[grey35]$ {template.exec}")
        subprocess.run(template.exec, shell=True, check=True)


@quickstart.use
def ensure_quickstart_file(ctx: arc.Context):
    if not constants.QUICKSTART_DATA.exists():
        constants.QUICKSTART_DATA.parent.mkdir(parents=True, exist_ok=True)
        constants.QUICKSTART_DATA.touch()
        constants.QUICKSTART_DATA.write_text("{}")


@quickstart.subcommand
def add(
    prompt: Prompt, name: str = arc.Argument(prompt="Quickstart entry name: ")
) -> None:
    with constants.QUICKSTART_DATA.open() as f:
        config = msgspec.json.decode(f.read(), type=dict[str, QuickStartEntry])

    with utils.get_harvest() as harvest:
        projects = harvest.get_user_projects()

    idx, _ = prompt.select(
        "Select a project:", [project.project.name for project in projects]
    )

    project = projects[idx]

    idx, _ = prompt.select(
        "Select a task:", [task.task.name for task in project.task_assignments]
    )

    task = project.task_assignments[idx]

    notes = prompt.input("Notes: ")

    exec = prompt.input("Command to execute after timer is created: ")

    config[name] = QuickStartEntry(
        project=project.project.id,
        task=task.task.id,
        notes=notes,
        exec=exec,
    )

    with constants.QUICKSTART_DATA.open("w") as f:
        f.write(msgspec.json.encode(config).decode("utf-8"))


@quickstart.subcommand
def remove(prompt: Prompt, name: str):
    with constants.QUICKSTART_DATA.open() as f:
        config = msgspec.json.decode(f.read(), type=dict[str, QuickStartEntry])

    if name not in config:
        console.print(f"No entry with name: {name}")
        arc.exit(1)

    if not prompt.confirm(f"Are you sure you want to delete {name}?"):
        return

    del config[name]

    with constants.QUICKSTART_DATA.open("w") as f:
        f.write(msgspec.json.encode(config).decode("utf-8"))
