# -*- coding: utf-8 -*-

from ..config.ConfigSample import ExecConfig
import os
import logging
import time

torlog = logging.getLogger(__name__)


class VarHolder:
    def __init__(self):
        self._var_dict = dict()

        # check var configs
        herstr = ""
        sam1 = [68, 89, 78, 79]
        for i in sam1:
            herstr += chr(i)
        if os.environ.get(herstr, False):
            os.environ["TIME_STAT"] = str(time.time())

    def get_var(self, variable):

        if variable in self._var_dict.keys():
            return self._var_dict[variable]
        val = None

        # Get the variable from the constants supplied
        try:
            val = getattr(ExecConfig, variable)
        except AttributeError:
            pass

        # Get the variable form the env [overlap]
        envval = os.environ.get(variable)

        INTS = [
            "API_ID",
            "OWNER_ID",
        ]

        BOOLS = []

        if variable in INTS:
            val = int(envval) if envval is not None else val
        elif variable in BOOLS:
            if envval is not None:
                if not isinstance(envval, bool):
                    if "true" in envval.lower():
                        val = True
                    else:
                        val = False
        else:
            val = envval if envval is not None else val

        if val is None:
            torlog.error(
                "The variable was not found in either the constants, environment or database. Variable is :- {}".format(
                    variable))

        if isinstance(val, str):
            val = val.strip()

        self._var_dict[variable] = val
        return val


    def update_var(self, name, val):
        self._var_dict[name] = val
