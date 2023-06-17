import arc
import keyring

from scythe_cli.application.console import console
from scythe_cli.harvest import Harvest


def get_harvest():
    access_token = keyring.get_password("scythe", "access_token")
    refresh_token = keyring.get_password("scythe", "refresh_token")

    if not access_token or not refresh_token:
        console.print("Please run [b]scythe init[/b] to authorize with Harvest.")
        arc.exit(1)

    harvest = Harvest(access_token, refresh_token)

    @harvest.on_refresh
    def on_refresh(access_token, refresh_token):
        keyring.set_password("scythe", "access_token", access_token)
        keyring.set_password("scythe", "refresh_token", refresh_token)

    return harvest
