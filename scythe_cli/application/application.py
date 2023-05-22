import arc
from arc import color
from arc.prompt import Prompt
from rich.console import Console

import toml
from scythe_cli import constants
from scythe_cli.config import Config
from scythe_cli.harvest import Harvest, HarvestError

arc.configure(
    environment="development",
    debug=True,
    present=arc.PresentConfig(color=arc.ColorConfig(accent=color.fg.hex("#fa5d00"))),
)

console = Console()


@arc.group
class SharedParams:
    config_path: arc.types.ValidPath = arc.Option(
        name="config",
        short="c",
        default=constants.CONFIG_FILE,
        desc="Config file to use",
    )

    def config(self):
        return Config.load(self.config_path)


@arc.command("scythe")
def scythe(params: SharedParams):
    from scythe_cli.ui.apps import ScytheApp

    app = ScytheApp(config=params.config())
    app.run()


@scythe.handle(HarvestError)  # type: ignore
def handle_api_error(ctx, ex: HarvestError):
    console.print(f"[red]Error: {ex.response.status_code}[/red]")
    console.print(ex.response.json()["error_description"])


@scythe.subcommand
def init(
    prompt: Prompt,
    params: SharedParams,
    account_id: str = arc.Argument(prompt="Harvest Account ID: "),
    token: str = arc.Argument(prompt="Harvest Token: "),
):
    """Initialize a new Scythe config file
    Create your API token at: [https://id.getharvest.com/developers].
    This will provide you the account id and token for your config file.
    """

    with Harvest(token, account_id) as client:
        with console.status("Verifying credentials..."):
            user = client.get_user()

        console.print(f"Hello, [b]{user.first_name} {user.last_name}[/b]!")
        console.print(f"Your email is: [b]{user.email}[/b]")

        if not prompt.confirm("Is this correct?"):
            console.print("Please try again.")
            return

        with console.status("Creating Config file..."):
            params.config_path.parent.mkdir(parents=True, exist_ok=True)
            config = Config(account_id=account_id, token=token, user_id=user.id)
            params.config_path.write_text(toml.dumps(config.dict(skip_defaults=True)))

        console.print("Config file created!")


@scythe.subcommand("quickstart", "qs")
def quickstart():
    ...


@quickstart.subcommand
def add():
    ...
