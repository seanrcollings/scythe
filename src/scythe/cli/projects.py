from arc import Context, namespace
from arc.color import effects, fg

from .. import helpers
from .. import utils
from ..harvest_api import HarvestApi

projects = namespace("projects")


@projects.subcommand("list")
@utils.config_required
def list_projects(ctx: Context):
    """Lists all of the user's projects and each project's tasks"""
    api: HarvestApi = ctx.api
    cache: utils.Cache = ctx.cache

    projects = (
        cache["projects"]
        or api.get_projects(ctx.config.user_id).json()["project_assignments"]
    )
    cache["projects"] = projects
    projects = helpers.Project.from_list(projects)

    for idx, project in enumerate(projects):
        print(f"{effects.BOLD}{fg.GREEN}({idx}) {project.name}{effects.CLEAR}")

        for task_idx, task in enumerate(project.tasks):
            print(f"\t({task_idx}) {task.name}")

    cache.save()
