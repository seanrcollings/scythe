import arc

from scythe_cli.ui.scythe import ScytheApp

arc.configure(environment="development", debug=True)


@arc.command("scythe")
def scythe():
    app = ScytheApp()
    app.run()
