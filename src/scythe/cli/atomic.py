from arc import namespace, Context

from ..harvest_api import HarvestApi
from .. import utils
from .. import helpers

AJ_INTERNAL_ID = 4212812
AJ_STANDUP_ID = 3442769
AJ_LEARNING_ID = 3336042

atomic = namespace("atomic")


@atomic.subcommand()
@utils.config_required
def standup(ctx: Context):
    """\
    Start Atomic Jolt's Standup
    Timer to today
    """
    api: HarvestApi = ctx.api
    cache: utils.Cache = ctx.cache

    projects = (
        cache["projects"]
        or api.get_projects(ctx.config.user_id).json()["project_assignments"]
    )
    cache["projects"] = projects
    projects = helpers.Project.from_list(projects)

    aj_internal = list(filter(lambda proj: proj.id == AJ_INTERNAL_ID, projects))[0]
    standup_task = list(
        filter(lambda task: task.id == AJ_STANDUP_ID, aj_internal.tasks)
    )[0]

    res = api.create_timer(project_id=aj_internal.id, task_id=standup_task.id)
    utils.print_valid_response(res, "Standup Timer Started!")
    cache["running_timer"] = res.json()["id"]
    cache.save()


@atomic.subcommand()
@utils.config_required
def training(ctx: Context):
    """\
    Start a timer for Atomic Jolt's
    weekly Training
    """
    api: HarvestApi = ctx.api
    cache: utils.Cache = ctx.cache

    projects = (
        cache["projects"]
        or api.get_projects(ctx.config.user_id).json()["project_assignments"]
    )
    cache["projects"] = projects
    projects = helpers.Project.from_list(projects)

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
