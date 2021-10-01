import functools

from arc.errors import ExecutionError
from arc import Context

from . import config_file, helpers
from .harvest_api import HarvestApi
from .utils import Cache


def config_required(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        if not config_file.exists():
            raise ExecutionError(
                "Config file must be present to run this command. Run 'scythe init'"
            )
        return func(*args, **kwargs)

    return decorator


def get_projects(func):
    """Convenience wrapper to
    get the list of projects.
    Embeds the projects into the
    ARC context object
    """

    @functools.wraps(func)
    def decorator(*args, **kwargs):
        context: Context = kwargs["ctx"]
        cache: Cache = context.cache
        api: HarvestApi = context.api

        if (projects := cache["projects"]) is None:
            projects = api.get_projects().json()["project_assignments"]
            cache["projects"] = projects
            cache.save()

        projects = helpers.Project.from_list(projects)
        context["projects"] = projects

        return func(*args, **kwargs)

    return decorator
