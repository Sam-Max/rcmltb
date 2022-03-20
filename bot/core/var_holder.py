#https://github.com/yash-dk/TorToolkit-Telegram/blob/master/tortoolkit/core/varholdern.py

import os
import logging
from bot.consts.ExecVars import Constants


log = logging.getLogger(__name__)


class VarHolder:
    def __init__(self):
        self._var_dict = dict()

    def get_var(self, variable):

        if variable in self._var_dict.keys():
            return self._var_dict[variable]

        val = None

        #Get the variable from the constants supplied
        try:
            val = getattr(Constants, variable)
        except AttributeError:pass

        # Get the variable form the env [overlap]
        envval = os.environ.get(variable)

        INTS = [
            "API_ID",
            "OWNER_ID",
            "TG_SPLIT_SIZE",
        ]

        BOOLS = ["UPLOAD_CANCEL"]
        
        if variable == "ALD_USR":
            if envval is not None:
                ald_user = envval.split(" ")
                ald_user2 = []
                if len(ald_user) > 0:
                    for i in range(0, len(ald_user)):
                        try:
                            ald_user2.append(int(ald_user[i]))
                        except ValueError:
                            log.error(f"Invalid allow user {ald_user[i]} must be a integer.")
                val = ald_user2
        elif variable in INTS:
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
            log.error(
                "The variable was not found in either the constants or environment Variable is :- {}".format(
                    variable))
            raise Exception("The variable was not found in either the constants or environment")
            
        if isinstance(val, str):
            val = val.strip()

        self._var_dict[variable] = val
        return val


    def update_var(self, name, val):
        self._var_dict[name] = val
