import arc
from scythe_cli import constants
from scythe_cli.config import Config

arc.configure(environment="development", debug=True)


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
    from scythe_cli.ui.scythe import ScytheApp

    app = ScytheApp(config=params.config())
    app.run()


@scythe.subcommand
def init(
    account_id: int = arc.Argument(prompt="Harvest Account ID: "),
    token: str = arc.Argument(prompt="Harvest Token: "),
):
    ...
