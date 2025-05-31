from discord.discord_filtered_read import get_messages
from discord.discord_write_attachment import send_attachment
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
    file_path = "data/podcast.mp3"
    message = (
        "Hey! Here's your podcast for this week. Lots lore-maxxing things to hear :)"
    )
    send_attachment(message=message, file_path=file_path)


if __name__ == "__main__":
    main()
