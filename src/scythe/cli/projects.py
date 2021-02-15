from arc import Context, namespace
from arc.color import effects, fg

from .. import helpers
from .. import decos

projects = namespace("projects")


@projects.subcommand("list")
@decos.config_required
@decos.get_projects
def list_projects(ctx: Context):
    """Lists all of the user's projects and each project's tasks"""
    project_list: list[helpers.Project] = ctx.projects

    for idx, project in enumerate(project_list):
        print(
            f"{effects.BOLD}{fg.GREEN}({idx}) {project.name} "
            f"{fg.BLACK.bright}({project.id}){effects.CLEAR}"
        )

        for task_idx, task in enumerate(project.tasks):
            print(f"\t({task_idx}) {task.name}")
