from discord_scripts.discord_filtered_read import get_messages
from discord_scripts.discord_write_attachment import send_attachment
from transcript.generate_transcript import generate_script_sync
from podcast.generate_podcast import generate_podcast_from_data


def main():
    # Get messages from discord
    if not get_messages():
        print("Failed to get messages")

    # Generate highlights of snippets based on audio and transcript.json
    generate_script_sync()

    # Create podcast
    generate_podcast_from_data()

    # Forward the podcast to Discord
    file_path = "data/initial_data_from_discord/voice_messages/voice-message.ogg"
    message = "demo for phi and raj"
    send_attachment(message=message, file_path=file_path)


if __name__ == "__main__":
    main()
