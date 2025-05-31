import discord
from config import config

DISCORD_TOKEN = config.DISCORD_TOKEN
SEND_CHANNEL_ID = config.SEND_CHANNEL_ID

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)


async def send_message(channel_id, message):
    """Sends a message to the specified Discord channel."""
    channel = client.get_channel(channel_id)
    if channel:
        try:
            await channel.send(message)
            print(f"Message sent to channel {channel_id}: {message}")
        except discord.errors.HTTPException as e:
            print(f"Failed to send message: {e}")
    else:
        print(f"Could not find channel with ID {channel_id}")


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    # Example usage: Send a message to the upload channel
    await send_message(SEND_CHANNEL_ID, "Hello, this is a test message!")
    await client.close()


client.run(DISCORD_TOKEN)
