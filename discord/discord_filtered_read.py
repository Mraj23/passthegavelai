import discord
import aiohttp
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
import asyncio

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

async def download_voice_attachment(attachment, session, download_folder):
    file_path = os.path.join(download_folder, attachment.filename)
    try:
        async with session.get(attachment.url) as resp:
            if resp.status == 200:
                with open(file_path, "wb") as f:
                    f.write(await resp.read())
                return attachment.filename
            else:
                print(f"Failed to download {attachment.filename}: HTTP status {resp.status}")
    except Exception as e:
        print(f"Error downloading {attachment.filename}: {e}")
    return None

async def fetch_recent_messages(channel, time_delta):
    cutoff_time = datetime.utcnow() - time_delta
    recent_messages = []
    async for message in channel.history(limit=None, after=cutoff_time):
        recent_messages.append(message)
    return recent_messages

# This function will now be executed directly by the bot's event loop
async def process_discord_messages_and_shutdown(client):
    """
    This is the core task that the bot will perform once it's ready.
    It fetches messages, downloads audio, saves data, and then shuts down the client.
    """
    env = load_env_vars() # Load env vars again, or pass them in from main
    create_folders() # Ensure folders exist

    print("Starting message processing task...")

    # Create aiohttp session within this task's scope for clean closure
    async with aiohttp.ClientSession() as session:
        try:
            channel = client.get_channel(env["UPLOAD_CHANNEL_ID"])
            if not channel:
                print(f"Could not find channel with ID {env['UPLOAD_CHANNEL_ID']}")
                # If channel not found, still close gracefully
                await client.close()
                client.loop.stop()
                return False

            user_audio_map = {}
            time_delta = timedelta(days=1)
            recent_messages = await fetch_recent_messages(channel, time_delta)

            for message in recent_messages:
                if message.author.bot:
                    continue

                author_name = message.author.name
                prettier_name = USERNAME_MAP.get(author_name, author_name)

                for attachment in message.attachments:
                    if attachment.content_type and "audio" in attachment.content_type:
                        print(f"Voice message found: {attachment.filename} from {author_name}")
                        filename = await download_voice_attachment(attachment, session, VOICE_FOLDER)
                        if filename:
                            if prettier_name not in user_audio_map:
                                user_audio_map[prettier_name] = []
                            user_audio_map[prettier_name].append(filename)

            output_list = []
            for name, files in user_audio_map.items():
                output_list.append({
                    "name": name,
                    "audio_files": files
                })

            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(output_list, f, indent=4)
            print(f"Data saved to {JSON_FILE}")

            return True # Indicate success

        except Exception as e:
            print(f"Error during bot task: {e}")
            return False # Indicate failure
        finally:
            # Ensure the client is closed and the loop stopped after the task finishes
            print("Processing complete. Shutting down Discord client...")
            await client.close()
            client.loop.stop() # This will stop the client.run() call

# No longer an async function
def main():
    env = load_env_vars()
    create_folders() # Create folders once at the start

    client = get_discord_client()

    @client.event
    async def on_ready():
        print(f"Logged in as {client.user} (ID: {client.user.id})")
        # Schedule the main processing task to run in the background
        # This allows on_ready to return, and the bot to fully start before
        # we try to close it.
        client.loop.create_task(process_discord_messages_and_shutdown(client))

    print("Attempting to start Discord client...")
    try:
        # client.run() is a blocking call that starts and manages the event loop.
        # It will exit when client.loop.stop() is called from within on_ready.
        client.run(env["DISCORD_TOKEN"])
        print("Discord client run loop has stopped.")
        # At this point, the task has completed and the client has closed.
        return True
    except discord.LoginFailure:
        print("Failed to log in. Please check your DISCORD_TOKEN.")
        return False
    except Exception as e:
        print(f"Error during client.run: {e}")
        return False

# if __name__ == "__main__":
#     if main():
#         print("Script finished successfully.")
#     else:
#         print("Script finished with errors.")