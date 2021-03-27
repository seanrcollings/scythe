import json
from arc import namespace


from .. import utils, decos, ui

running = namespace("running")


@running.base(context={})
@decos.config_required
def base(ctx: utils.ScytheContext, big: bool, clock_only: bool, interval: int = 10):
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
@running.subcommand()
@decos.config_required
def waybar(ctx: utils.ScytheContext):
    timer = ctx.cache["running_timer"]
    harvest_logo = '<span size="larger" background="#f36c00" foreground="#fff" weight="bold"> H </span>'
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
    else:
        print(
            json.dumps(
                {
                    "text": f'{harvest_logo} {utils.format_time(*utils.parse_time(timer["hours"]))}',
                    "alt": "",
                    "class": "active",
                    "tooltip": f"{timer['task']['name']} - {timer['notes']}",
                    "percentage": 0,
                }
            ),
            end="",
        )

    utils.sync_running_timer(ctx.api, ctx.cache)
