import webbrowser
from arc import namespace, Context
from arc.color import fg, effects

from ..harvest_api import HarvestApi
from .. import utils
from .. import decos
from .. import helpers

AJ_INTERNAL_ID = 4212812
AJ_STANDUP_ID = 3442769
AJ_LEARNING_ID = 3336042


atomic = namespace("atomic")


@atomic.subcommand()
@decos.config_required
@decos.get_projects
def standup(launch: bool, ctx: Context):
    """\
    Start Atomic Jolt's Standup
    Timer to today

    Arguments:
    --launch  Will launch the STANDUP_LINK provided in
              in the config file in the default browser
    """
    api: HarvestApi = ctx.api
    cache: utils.Cache = ctx.cache
    config: utils.Config = ctx.config
    projects: list[helpers.Project] = ctx.projects

    aj_internal = list(filter(lambda proj: proj.id == AJ_INTERNAL_ID, projects))[0]
    standup_task = list(
        filter(lambda task: task.id == AJ_STANDUP_ID, aj_internal.tasks)
    )[0]

    res = api.create_timer(project_id=aj_internal.id, task_id=standup_task.id)
    utils.print_valid_response(res, "Standup Timer Started!")
    cache["running_timer"] = res.json()["id"]
    cache.save()
    if launch:
        if config.standup_link is not None:
            webbrowser.open_new_tab(config.standup_link)
        else:
            print(
                f"{fg.RED}No STANDUP_LINK present in config file to open{effects.CLEAR}"
            )


@atomic.subcommand()
@decos.config_required
@decos.get_projects
def training(launch: bool, ctx: Context):
    """\
    Start a timer for Atomic Jolt's
    weekly Training

    Arguments:
    --launch  Will launch the TRAINING_LINK provided in
              in the config file in the default browser
    """
    api: HarvestApi = ctx.api
    cache: utils.Cache = ctx.cache
    config: utils.Config = ctx.config
    projects: list[helpers.Project] = ctx.projects

    aj_internal = list(filter(lambda proj: proj.id == AJ_INTERNAL_ID, projects))[0]
    learning_task = list(
        filter(lambda task: task.id == AJ_LEARNING_ID, aj_internal.tasks)
    )[0]

    res = api.create_timer(
        project_id=aj_internal.id, task_id=learning_task.id, notes="Training"
    )
    utils.print_valid_response(res, "Training Time Started!")
    cache["running_timer"] = res.json()["id"]
    cache.save()

    if launch:
        if config.training_link is not None:
            webbrowser.open_new_tab(config.training_link)
        else:
            print(
                f"{fg.RED}No TRAINING_LINK present in config file to open{effects.CLEAR}"
            )
