import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    DOWNLOAD_FOLDER = os.getenv("DOWNLOAD_FOLDER")
    SERVER_ID = int(os.getenv("SERVER_ID")) if os.getenv("SERVER_ID") else None
    UPLOAD_CHANNEL_ID = (
        int(os.getenv("UPLOAD_CHANNEL_ID")) if os.getenv("UPLOAD_CHANNEL_ID") else None
    )
    SEND_CHANNEL_ID = (
        int(os.getenv("SEND_CHANNEL_ID")) if os.getenv("SEND_CHANNEL_ID") else None
    )


config = Config()
