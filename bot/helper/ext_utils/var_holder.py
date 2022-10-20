from bot import OWNER_ID, rclone_user_dict, MULTI_RCLONE_CONFIG

def get_rc_user_value(var, user_id):
    if MULTI_RCLONE_CONFIG:    
        user_id= str(user_id)
    else:
        user_id= str(OWNER_ID)
    if var_dict := rclone_user_dict.get(user_id, False):
        if value := var_dict.get(var, False):
            return value
        else:
            return ""
    else:
        if var.endswith("DIR"):
            return "/"
        else:
            return ""

def update_rc_user_var(var, value, user_id):
    if MULTI_RCLONE_CONFIG:    
        user_id= str(user_id)
    else:
        user_id= str(OWNER_ID)
    if var_dict := rclone_user_dict.get(user_id, False):
        rclone_user_dict[user_id][var] = value
    else:
        rclone_user_dict[user_id] = {var:value}