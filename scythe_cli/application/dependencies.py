from scythe_cli.stack import TimerStack
from scythe_cli import constants


def get_stack():
    return TimerStack(constants.STACK_DATA)
