from arc import namespace

from .. import utils


stats = namespace("stats")


@stats.subcommand()
@utils.config_required
def today():
    """Prints out stats for today's projects"""
