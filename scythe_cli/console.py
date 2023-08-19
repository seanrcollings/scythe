from rich.console import Console


class ScytheConsole(Console):
    def ok(self, *objects, **kwargs):
        self.print(" [green]✔[/green] ", *objects, **kwargs)


console = ScytheConsole()
