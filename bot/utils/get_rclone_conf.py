import os

async def get_config():
        config = os.path.join(os.getcwd(), 'rclone.conf')
        if config is not None:
            if isinstance(config, str):
                if os.path.exists(config):
                    return config

        return None