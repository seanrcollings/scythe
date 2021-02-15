from arc import namespace

from .. import decos


stats = namespace("stats")


@stats.subcommand()
@decos.config_required
def today():
    """Prints out stats for today's projects"""
