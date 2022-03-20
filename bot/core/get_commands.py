# Adapted from:
# https://github.com/yash-dk/TorToolkit-Telegram/blob/master/tortoolkit/core/getCommand.py

from ..consts.DefaultCommands import Commands
import logging

torlog = logging.getLogger(__name__)


def get_command_tele(command):
    cmd = None

    # Get the command from the constants supplied
    try:
        cmd = getattr(Commands, command)
        torlog.debug(f"Getting the command {command} from file:- {cmd}")
    except AttributeError:
        pass

    if cmd is None:
        torlog.debug(f"None Command Error occured for command {command}")
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
        torlog.debug(f"Getting the command {command} from file:- {cmd}")
    except AttributeError:
        pass

    if cmd is None:
        torlog.debug(f"None Command Error occured for command {command}")
        raise Exception(
            "The command was not found in either the constants, environment. Command is :- {}".format(
                command))

    cmd = cmd.strip("/")             

    return cmd