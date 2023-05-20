import arc
from scythe_cli import constants
from scythe_cli.config import Config
from scythe_cli.ui.scythe import ScytheApp

arc.configure(environment="development", debug=True)


@arc.command("scythe")
def scythe(
    *,
    config_path: arc.types.ValidPath = arc.Option(
        name="config",
        short="c",
        default=constants.CONFIG_FILE,
        desc="Config file to use",
    ),
):
    config = Config.load(config_path)
    app = ScytheApp(config=config)
    app.run()
