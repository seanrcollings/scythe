import arc
from rich.table import Table

from scythe_cli import constants, utils
from scythe_cli.console import console
from scythe_cli.stack import TimerStack

stackcmd = arc.namespace(
    "stack",
    desc="Each time a timer is started it is pushed onto the top of the timer stack. You can use this stack to start old timers",
)


def get_stack():
    return TimerStack(constants.STACK_DATA)


@stackcmd.subcommand("list", "l")
def list_command(stack: TimerStack = arc.Depends(get_stack)) -> None:
    """List timers in stack"""
    table = Table("Index", "Project", "Task", "Notes", "Time")

    for idx, timer in enumerate(stack):
        table.add_row(
            str(idx),
            timer["project"],
            timer["task"],
            timer["notes"],
            utils.display_time(timer["time"]),
        )

    console.print(table)


@stackcmd.subcommand("clear", "c")
def clear_stack(stack: TimerStack = arc.Depends(get_stack)) -> None:
    """Clear stack"""
    stack.clear()
    console.ok("Stack cleared.")


@stackcmd.subcommand("remove", "r")
def remove_entry(
    index: int = arc.Argument(desc="Index of the timer to remove from the stack"),
    stack: TimerStack = arc.Depends(get_stack),
) -> None:
    """Remove entry from stack"""
    if len(stack) <= index:
        console.print("Invalid index.")
        arc.exit(1)

    stack.pop(index)
    console.ok("Removed entry from stack.")


@stackcmd.subcommand("start", "s")
def start(
    index: int = arc.Argument(desc="Index of the timer in the stack to start"),
    stack: TimerStack = arc.Depends(get_stack),
) -> None:
    """Start timer from stack"""
    if len(stack) <= index:
        console.print("Invalid index.")
        arc.exit(1)

    timer = stack[index]

    with utils.get_harvest() as harvest, console.status("Staring timer..."):
        harvest.start_timer(timer["id"])

    # Push it to put it back on top
    stack.push(timer)

    console.ok("Timer started!")
