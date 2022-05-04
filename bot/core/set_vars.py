from .. import SessionVars


def set_val(name, variable):
    return SessionVars.update_var(name, variable)
