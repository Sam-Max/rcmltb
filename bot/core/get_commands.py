# Adapted from:
# https://github.com/yash-dk/TorToolkit-Telegram/blob/master/tortoolkit/core/getCommand.py

from bot import LOGGER
from bot.consts.DefaultCommands import Commands


def get_command_tele(command):
    cmd = None

    # Get the command from the constants supplied
    try:
        cmd = getattr(Commands, command)
    except AttributeError:
        pass

    if cmd is None:
        LOGGER.error(f"None Command Error occured for command {command}")
        raise Exception(
            "The command was not found in either the constants, environment. Command is :- {}".format(
                command))

    cmd = cmd.strip("/")

    return f"/{cmd}"

def get_command_pyro(command):
    cmd = None

    # Get the command from the constants supplied
    try:
        cmd = getattr(Commands, command)
    except AttributeError:
        pass

    if cmd is None:
        LOGGER.debug(f"None Command Error occured for command {command}")
        raise Exception(
            "The command was not found in either the constants, environment. Command is :- {}".format(
                command))

    cmd = cmd.strip("/")             

    return cmd