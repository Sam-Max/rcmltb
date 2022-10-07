from bot import rclone_user_dict

def get_rc_user_value(var, user_id):
    user_id= str(user_id)     
    var_dict = rclone_user_dict.get(user_id, False)
    if var_dict:
        value = var_dict.get(var, False)
        if value:
            return value
        else:
            return ""
    else:
        if var.endswith("DIR"):
            return "/"
        else:
            return ""

def update_rc_user_var(var, value, user_id):
    user_id= str(user_id)   
    var_dict = rclone_user_dict.get(user_id, False)
    if var_dict:
        rclone_user_dict[user_id][var] = value
    else:
        rclone_user_dict[user_id] = {var:value}