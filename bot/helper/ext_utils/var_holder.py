from os import environ

class _EnvVarHolder():
    def __init__(self):
         pass
        
    def get_var(self, var):
        return environ.get(var, '')

    def set_var(self, var, value):
        environ[var]= str(value)
    
EnvVarHolder = _EnvVarHolder()

def get_env_var(var):
     return EnvVarHolder.get_var(var)

def set_env_var(var, value):
     return EnvVarHolder.set_var(var, value)

class _RcloneVarHolder:
    def __init__(self):
        self._rclone_var_dict = {}

    def get_var(self, var, user_id):
        user_id= str(user_id)     
        user = self._rclone_var_dict.get(user_id)
        if user is not None:
            var = user.get(var)
            if var is not None:
                return var
            else:
                return ""
        else:
            if var.endswith("DIR"):
                return "/"
            else:
                return ""

    def set_var(self, var, value, user_id):
        user_id= str(user_id)   
        user = self._rclone_var_dict.get(user_id)
        if user is not None:
            self._rclone_var_dict[user_id][var] = value
        else:
            self._rclone_var_dict[user_id] = {var:value}
    
RcloneVarHolder = _RcloneVarHolder()

def get_rclone_var(var, user_id):
     return RcloneVarHolder.get_var(var, user_id)

def set_rclone_var(var, value, user_id):
     return RcloneVarHolder.set_var(var, value, user_id)