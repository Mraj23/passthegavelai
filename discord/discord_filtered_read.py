import discord
import aiohttp
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Map of discord usernames to prettier names
USERNAME_MAP = {
    "lennyhuang": "Len",
    "Raj": "Raj",
    "Phi": "Phi",
    # Add more mappings as needed
}

DATA_FOLDER = "ptg_discord_data"
VOICE_FOLDER = os.path.join(DATA_FOLDER, "voice_messages")
JSON_FILE = os.path.join(DATA_FOLDER, "ptg_discord_data.json")

def load_env_vars():
    load_dotenv()
    return {
        "DISCORD_TOKEN": os.getenv("DISCORD_TOKEN"),
        "SERVER_ID": int(os.getenv("SERVER_ID")),
        "UPLOAD_CHANNEL_ID": int(os.getenv("UPLOAD_CHANNEL_ID")),
    }

def create_folders():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    if not os.path.exists(VOICE_FOLDER):
        os.makedirs(VOICE_FOLDER)

def get_discord_client():
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True  # Needed to read message contents
    return discord.Client(intents=intents)

async def download_voice_attachment(attachment, download_folder):
    file_path = os.path.join(download_folder, attachment.filename)
    async with aiohttp.ClientSession() as session:
        async with session.get(attachment.url) as resp:
            if resp.status == 200:
                with open(file_path, "wb") as f:
                    f.write(await resp.read())
                return attachment.filename
    return None

async def fetch_recent_messages(channel, time_delta):
    cutoff_time = datetime.utcnow() - time_delta
    recent_messages = []
    async for message in channel.history(limit=None, after=cutoff_time):
        recent_messages.append(message)
    return recent_messages

async def get_messages():
    """
    Downloads voice message audio files from the specified Discord channel
    into ptg_discord_data/voice_messages and creates ptg_discord_data.json
    with structured output mapping prettier names to audio files.

    Returns:
        success (bool): True if completed successfully, False otherwise.
    """
    env = load_env_vars()
    create_folders()
    client = get_discord_client()

    # Data structure to hold mapping of prettier names to audio files
    user_audio_map = {}

    # Event to signal completion
    done_event = discord.utils.Event()

    @client.event
    async def on_ready():
        try:
            channel = client.get_channel(env["UPLOAD_CHANNEL_ID"])
            if not channel:
                print(f"Could not find channel with ID {env['UPLOAD_CHANNEL_ID']}")
                done_event.set()
                return

            # Fetch messages from past 1 day (can be adjusted)
            time_delta = timedelta(days=1)
            recent_messages = await fetch_recent_messages(channel, time_delta)

            for message in recent_messages:
                if message.author.bot:
                    continue
                author_name = str(message.author)
                prettier_name = USERNAME_MAP.get(author_name, author_name)
                for attachment in message.attachments:
                    if attachment.content_type and "audio" in attachment.content_type:
                        print(f"Voice message found: {attachment.filename} from {author_name}")
                        filename = await download_voice_attachment(attachment, VOICE_FOLDER)
                        if filename:
                            if prettier_name not in user_audio_map:
                                user_audio_map[prettier_name] = []
                            user_audio_map[prettier_name].append(filename)

            # Prepare JSON output
            output_list = []
            for name, files in user_audio_map.items():
                output_list.append({
                    "name": name,
                    "audio_files": files
                })

            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(output_list, f, indent=4)

            print(f"Data saved to {JSON_FILE}")
        except Exception as e:
            print(f"Error during get_messages: {e}")
        finally:
            done_event.set()
            await client.close()

    await client.start(env["DISCORD_TOKEN"])
    await done_event.wait()
    return True
