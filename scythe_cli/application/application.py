import typing as t
import base64
import webbrowser
import arc
from arc import color
from arc.prompt import Prompt
import keyring

from scythe_cli.harvest import AsyncHarvest, Harvest, HarvestError
from .console import console
from . import utils

from .quickstart import quickstart

arc.configure(
    environment="development",
    debug=True,
    present=arc.PresentConfig(color=arc.ColorConfig(accent=color.fg.hex("#fa5d00"))),
)


@arc.command("scythe")
def scythe():
    from scythe_cli.ui.apps import ScytheApp

    access_token = keyring.get_password("scythe", "access_token")
    refresh_token = keyring.get_password("scythe", "refresh_token")

    if not access_token or not refresh_token:
        console.print("Please run [b]scythe init[/b] to authorize with Harvest.")
        arc.exit(1)

    harvest = AsyncHarvest(access_token, refresh_token)

    @harvest.on_refresh
    def on_refresh(access_token, refresh_token):
        keyring.set_password("scythe", "access_token", access_token)
        keyring.set_password("scythe", "refresh_token", refresh_token)

    app = ScytheApp(harvest=harvest)
    app.run()


@scythe.subcommand
def init(prompt: Prompt):
    """Initialize Scythe with your Harvest credentials.
    Will ask you to log in to Harvest & authorize Scythe."""

    console.print("Opening browser to authorize Scythe with Harvest...")
    webbrowser.open("https://scythe.seancollings.dev")

    code = prompt.input("Code: ")
    try:
        decoded = base64.b64decode(code)
        access_token, refresh_token = decoded.decode("utf-8").split("+")
    except Exception:
        console.print("Invalid code")
        arc.exit(1)

    with Harvest(access_token, refresh_token) as client:
        with console.status("Verifying credentials..."):
            user = client.get_user()

        console.print(f"Hello, [b]{user.first_name} {user.last_name}[/b]!")
        console.print(f"Your email is: [b]{user.email}[/b]")

        if not prompt.confirm("Is this correct?"):
            console.print("Please try again.")
            return

        keyring.set_password("scythe", "access_token", access_token)
        keyring.set_password("scythe", "refresh_token", refresh_token)
        console.print("Credentials saved to keyring!")


@scythe.subcommand
def projects():

    with utils.get_harvest() as harvest, console.status("Fetching projects..."):
        projects = harvest.get_user_projects()

    for project in projects:
        console.print(f"[b]{project.project.name}[/b] [gray35]({project.project.id})")

        for task in project.task_assignments:
            console.print(f"     {task.task.name} [gray35]({task.task.id})")


@scythe.handle(HarvestError)  # type: ignore
def handle_api_error(ctx, ex: HarvestError):
    console.print(f"[red]Error: {ex.response.status_code}[/red]")
    console.print(
        ex.response.json().get("error_description")
        or ex.response.json().get("message")
        or ex.response.text
    )


scythe.subcommand(quickstart, "qs")
