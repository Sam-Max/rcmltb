# Adapted from:
# https://github.com/yash-dk/TorToolkit-Telegram/blob/master/tortoolkit/core/varholdern.py


import logging
from bot.core.DefaultVariables import DefaultVars

class VarHolder:
    def __init__(self):
        self._var_dict = dict()

    def get_var(self, var):

        #Get the variable from dictionary
        if var in self._var_dict.keys():
            return self._var_dict[var]

        #Get the variable from the default variables
        val = None
        try:
            val = getattr(DefaultVars, var)
        except AttributeError:
            pass

        if val is None:
            logging.info("Variable not found :- {}".format(var))
            
        if isinstance(val, str):
            val = val.strip()

        self._var_dict[var] = val
        return val

    def set_var(self, name, val):
        self._var_dict[name] = val
