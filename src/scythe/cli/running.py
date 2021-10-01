import datetime
import json
from arc import namespace, command

from .. import utils, decos, ui, helpers


def hours_minutes(td: datetime.timedelta):
    return td.seconds // 3600, (td.seconds // 60) % 60


@command()
@decos.config_required
def running(ctx: utils.ScytheContext, big: bool, clock_only: bool, interval: int = 10):
    """\
    Displays the currently running timer

    Arguments:
    interval=VALUE Interval in seconds which to refresh data
                   by calling the API. Defaults to 10

    --big          Use larger clock characters
    --clock_only   Only display the clock
    """

    size = "big" if big else "small"
    message = ui.running_ui(ctx.api, interval, size, clock_only)
    if message is not None:
        print(message)


# Setup
# Retrieve the current running timer
# Cache off the last time retrieved, the current time on the timer, and the last time udpated
# each call, increase the current time in the cache and update the last time updated to NOW
# Every x amount of minutes, recall the api to assert that we're still in sync
# Possibly update the above command to do the same?
HARVEST_LOGO = '<span background="#f36c00" foreground="#fff" weight="bold"> H </span>'


@running.subcommand()
@decos.config_required
def waybar(ctx: utils.ScytheContext):
    """\
    Outputs a JSON encoded representation of
    the currently running timer to be used with
    waybar (https://github.com/Alexays/Waybar)
    """
    timer = ctx.cache["running_timer"]
    if not timer:
        print(
            json.dumps(
                {
                    "text": "",
                    "alt": "",
                    "tooltip": "No Timer Currenlty Running",
                    "percentage": 0,
                }
            ),
            end="",
        )
        return
    timer = helpers.Timer(timer)
    now = datetime.datetime.now().time()
    updated_at = ctx.cache.updated_at("running_timer")
    # We convert the times all into minutes and get the difference between them
    # Then we divide it by 60 to get the minutes as a % of an hour, which is
    # the way that Harvest stores their timers
    minutes_delta = (
        (now.hour * 60 + now.minute) - (updated_at.hour * 60 + updated_at.minute)
    ) / 60

    hours, minutes = utils.parse_time(timer.hours + minutes_delta)

    print(
        json.dumps(
            {
                "text": f"{HARVEST_LOGO} {utils.format_time(hours, minutes)}",
                "alt": "",
                "class": "active",
                "tooltip": f"{timer.task['name']} - {timer.notes}",
                "percentage": 0,
            }
        ),
        end="",
    )
