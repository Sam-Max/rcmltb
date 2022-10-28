from bot import OWNER_ID, config_dict

rclone_dict = {}

def get_rclone_val(var, user_id):
    if config_dict['MULTI_RCLONE_CONFIG']:   
        user_id= str(user_id)
    else:
        user_id= str(OWNER_ID)
    if rclone_var_dict := rclone_dict.get(user_id, False):
        if value := rclone_var_dict.get(var, False):
            return value
        else:
            return ""
    else:
        return ""

def update_rclone_var(var, value, user_id):
    if config_dict['MULTI_RCLONE_CONFIG']:     
        user_id= str(user_id)
    else:
        user_id= str(OWNER_ID)
    if rclone_dict.get(user_id, False):
        rclone_dict[user_id][var] = value
    else:
        rclone_dict[user_id] = {var:value}