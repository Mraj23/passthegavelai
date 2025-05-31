import discord
import aiohttp
import os
from config import config

DISCORD_TOKEN = config.DISCORD_TOKEN
DOWNLOAD_FOLDER = config.DOWNLOAD_FOLDER
SERVER_ID = config.SERVER_ID
UPLOAD_CHANNEL_ID = config.UPLOAD_CHANNEL_ID

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Needed to read message contents

client = discord.Client(intents=intents)

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    channel = client.get_channel(UPLOAD_CHANNEL_ID) # or client.get_channel(int(CHANNEL_ID)) if given as str without int

    if channel:
        async for message in channel.history(limit=10): # Fetch last 10 messages
            print(f'{message.author}: {message.content}')
            await on_message(message)
    else:
        print(f"Could not find channel with ID {UPLOAD_CHANNEL_ID}")
    await client.close()  # Disconnect after reading messages

async def on_message(message):
    if message.author.bot:
        return

    # Check if message has attachments
    for attachment in message.attachments:
        if attachment.content_type and "audio" in attachment.content_type:
            print(f"Voice message found: {attachment.filename}")
            await download_voice(attachment)

async def download_voice(attachment):
    file_path = os.path.join(DOWNLOAD_FOLDER, attachment.filename)
    async with aiohttp.ClientSession() as session:
        async with session.get(attachment.url) as resp:
            if resp.status == 200:
                with open(file_path, "wb") as f:
                    f.write(await resp.read())
                print(f"Downloaded to {file_path}")

client.run(DISCORD_TOKEN)
