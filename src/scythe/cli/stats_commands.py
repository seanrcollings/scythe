from arc import namespace

from .. import utils

from . import stats


@stats.subcommand()
@utils.config_required
def today():
    """Prints out stats for today's projects"""
