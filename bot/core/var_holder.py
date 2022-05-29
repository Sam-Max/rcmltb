#https://github.com/yash-dk/TorToolkit-Telegram/blob/master/tortoolkit/core/varholdern.py

import os
import logging
from bot.consts.ExecVars import Constants

LOGGER = logging.getLogger(__name__)

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
            "EDIT_SLEEP_SECS"
        ]

        BOOLS = [
            "UPLOAD_CANCEL",
            "IS_ZIP",
            "EXTRACT",
        ]
        
        if variable == "ALLOWED_CHATS":
            if envval is not None:
                achats= envval.split(" ")
                achats_second= []
                for chat in achats:
                    achats_second.append(int(chat))
                val = achats_second
        elif variable == "ALLOWED_USERS":
            if envval is not None:
                ausers = envval.split(" ")
                ausers_second= []
                logging.info(ausers)
                for user in ausers:
                    ausers_second.append(int(user))
                val = ausers_second
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
            LOGGER.error("The variable was not found in either the constants or environment, variable is :- {}".format(variable))
            
        if isinstance(val, str):
            val = val.strip()

        self._var_dict[variable] = val
        return val


    def update_var(self, name, val):
        self._var_dict[name] = val
