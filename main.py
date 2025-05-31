from discord.discord_filtered_read import get_messages

def main():
    if not get_messages():
        print("Failed to get messages")
        return


if __name__ == "__main__":
    main()