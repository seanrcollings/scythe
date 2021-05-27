import datetime
import subprocess

from arc import namespace, Context
from arc.present import Box, Table
from arc.color import fg, effects

from ..clock import clock
from .. import decos, utils
from ..harvest_api import HarvestApi

stats = namespace("stats")


def get_breakdown_str(projects: list[dict], heading_string: str):
    total_hours, total_minutes = 0, 0
    for project in projects:
        hours, minutes = utils.parse_time(project["total_hours"])
        total_hours += hours
        total_minutes += minutes
        if total_minutes > 59:
            total_hours += 1
            total_minutes -= 60

    total_time_display = (
        f"{fg.GREEN}"
        f"{utils.clean(Box(clock(total_hours, total_minutes), justify='center'))}"
        f"{effects.CLEAR}"
    )
    breakdown_display = Table(
        ["Project Name", "Time"],
        [(project["project_name"], project["total_hours"]) for project in projects],
    )

    return f"{heading_string}\nTotal Hours Worked:\n{total_time_display}\n{breakdown_display}"


@stats.subcommand()
@decos.config_required
def breakdown(text: bool, ctx: Context):
    """\
    Displays a quick breakdown of the
    hours worked in the last day, 7 days, and 30 days

    Arguments:
    --text    Normally this command pipes it's output to
              less, use this if you just want it to print
              it's output to stdout
    """
    api: HarvestApi = ctx.api
    today_date = datetime.datetime.today()
    get_start = lambda x: (today_date - datetime.timedelta(x)).strftime("%Y%m%d")
    end = today_date.strftime("%Y%m%d")

    content = ""
    # Today
    results = api.get(f"/reports/time/projects?from={end}&to={end}").json()["results"]
    content += get_breakdown_str(results, "Today's Breakdown")

    # Last Week
    start = get_start(7)
    results = api.get(f"/reports/time/projects?from={start}&to={end}").json()["results"]
    content += get_breakdown_str(results, "7 Days Breakdown")

    # Last Month
    start = get_start(30)
    results = api.get(f"/reports/time/projects?from={start}&to={end}").json()["results"]
    content += get_breakdown_str(results, "30 Days Breakdown")

    if text:
        print(content)
    else:
        less = subprocess.Popen(["less", "-r"], stdin=subprocess.PIPE)
        less.communicate(content.encode("utf-8"))


# @stats.subcommand()
# @decos.config_required
# def today():
#     """Breakdown of the current
#     day's hour count by project and task"""
