import datetime
import arc
from rich.table import Table
from rich.panel import Panel
from rich.console import Group

from scythe_cli.console import console
from scythe_cli import utils


timer = arc.namespace("timer", desc="Timer utilities")

today = datetime.datetime.now().strftime("%Y-%m-%d")


@timer.subcommand("list")
def list_timers(
    from_date: str = arc.Option(name="from", short="f", default=today),
    to_date: str = arc.Option(name="to", short="t", default=today),
):
    with utils.get_harvest() as harvest, console.status("Fetching timers..."):
        timers = harvest.get_time_entries(params={"from": from_date, "to": to_date})

    table = Table("ID", "Project", "Task", "Notes", "Time")

    for timer in timers:
        table.add_row(
            str(timer.id),
            timer.project.name,
            timer.task.name,
            timer.notes or "",
            utils.display_time(timer.seconds()),
        )

    console.print(table)


@timer.subcommand
def running():
    with utils.get_harvest() as harvest:
        timer = harvest.get_running_time_entry()

        if timer is None:
            console.print("No running timer")
            return

        group = Group(
            f"[b]Project:[/b] {timer.project.name}",
            f"[b]Task:[/b]    {timer.task.name}",
            f"[b]Notes:[/b]   {timer.notes or '-'}",
            f"[b]Time:[/b]    {utils.display_time(timer.seconds())}",
        )
        console.print(Panel(group, title="Running Timer", expand=False))


@timer.subcommand
def stop():
    with utils.get_harvest() as harvest:
        timer = harvest.get_running_time_entry()

        if timer is None:
            console.print("No running timer")
            arc.exit(0)

        harvest.stop_timer(timer.id)
        console.print("[green]✓ Stopped timer!")
