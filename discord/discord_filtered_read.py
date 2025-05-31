import discord
import aiohttp
import os
import json
from datetime import datetime, timedelta
from config import config


def create_folders():
    data_folder = config.DOWNLOAD_FOLDER
    voice_folder = os.path.join(data_folder, "voice_messages")
    voice_metadata_file = os.path.join(data_folder, "ptg_discord_data.json")
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    if not os.path.exists(voice_folder):
        os.makedirs(voice_folder)
    return voice_folder, voice_metadata_file


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
                print(
                    f"Failed to download {attachment.filename}: status {resp.status}"
                )
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
    voice_folder, voice_metadata_file = create_folders()  # Ensure folders exist

    print("Starting message processing task...")

    # Create aiohttp session within this task's scope for clean closure
    async with aiohttp.ClientSession() as session:
        try:
            channel = client.get_channel(config.UPLOAD_CHANNEL_ID)
            if not channel:
                print(f"Could not find channel with ID {config.UPLOAD_CHANNEL_ID}")
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

                for attachment in message.attachments:
                    if attachment.content_type and "audio" in attachment.content_type:
                        print(
                            f"Voice message: {attachment.filename} from {author_name}"
                        )
                        filename = await download_voice_attachment(
                            attachment, session, voice_folder
                        )
                        if filename:
                            if author_name not in user_audio_map:
                                user_audio_map[author_name] = []
                            user_audio_map[author_name].append(filename)

            output_list = []
            for name, files in user_audio_map.items():
                output_list.append({"name": name, "audio_files": files})

            with open(voice_metadata_file, "w", encoding="utf-8") as f:
                json.dump(output_list, f, indent=4)
            print(f"Data saved to {voice_metadata_file}")

            return True  # Indicate success

        except Exception as e:
            print(f"Error during bot task: {e}")
            return False  # Indicate failure
        finally:
            # Ensure the client is closed and the loop stopped after the task finishes
            print("Processing complete. Shutting down Discord client...")
            await client.close()
            client.loop.stop()  # This will stop the client.run() call


# No longer an async function
def get_messages():
    create_folders()  # Create folders once at the start

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
        client.run(config.DISCORD_TOKEN)
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
