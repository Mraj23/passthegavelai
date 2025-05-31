import discord
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SEND_CHANNEL_ID = int(os.getenv("SEND_CHANNEL_ID"))

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

async def send_message(message: str, filename: str):
    """Sends a message with an attached file to the configured Discord channel."""
    channel = client.get_channel(SEND_CHANNEL_ID)
    if channel:
        try:
            with open(filename, "rb") as file:
                discord_file = discord.File(file)
                await channel.send(content=message, file=discord_file)
            print(f"Message and file '{filename}' sent to channel {SEND_CHANNEL_ID}")
        except FileNotFoundError:
            print(f"File not found: {filename}")
        except discord.errors.HTTPException as e:
            print(f"Failed to send message: {e}")
    else:
        print(f"Could not find channel with ID {SEND_CHANNEL_ID}")

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    # Example usage: send a test message with a file
    await send_message("Hello, this is a test message with file!", "testfile.txt")
    # Close the client after sending message(s)
    await client.close()

def send_attachment(*, message: str, file_path: str):
    """Run the client and send the message with file."""
    async def send_and_close():
        channel = client.get_channel(SEND_CHANNEL_ID)
        if channel:
            try:
                with open(file_path, "rb") as file:
                    discord_file = discord.File(file)
                    await channel.send(content=message, file=discord_file)
                print(f"Message and file '{file_path}' sent to channel {SEND_CHANNEL_ID}")
            except FileNotFoundError:
                print(f"File not found: {file_path}")
            except discord.errors.HTTPException as e:
                print(f"Failed to send message: {e}")
        else:
            print(f"Could not find channel with ID {SEND_CHANNEL_ID}")
        await client.close()

    @client.event
    async def on_ready():
        print(f'We have logged in as {client.user}')
        await send_and_close()

    client.run(DISCORD_TOKEN)