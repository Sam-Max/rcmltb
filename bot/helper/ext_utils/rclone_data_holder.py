rclone_dict = {}


def get_rclone_data(key, user_id):
    value_dict = rclone_dict.get(user_id, {})
    return value_dict.get(key, "")


def update_rclone_data(key, value, user_id):
    if user_id in rclone_dict:
        rclone_dict[user_id][key] = value
    else:
        rclone_dict[user_id] = {key: value}
