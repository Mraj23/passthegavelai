import sys
from discord.discord_filtered_read import get_messages
from discord.discord_write_attachment import send_attachment

def main():
    # Get messages from discord
    if not get_messages():
        print("Failed to get messages")

    # TODO: Generate highlights of snippets based on audio

    # TODO: Create a podcast transcript with snippets embedded

    # TODO: Generate audio for podcast based on transcript

    # Forward the podcast to Discord
    file_path = "data/initial_data_from_discord/voice_messages/voice-message.ogg"
    message = "demo for phi and raj"
    send_attachment(message=message, file_path=file_path)

if __name__ == "__main__":
    main()