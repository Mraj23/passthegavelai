# Discord Bot

https://discord.com/developers/applications/1378387843482652702

Need to give permissions to read / write etc via OAuth2 Section and Message Content Intent

# Examples

![bot-perms](readme_images/bot-perms.png)

![message-intents](readme_images/message-intents.png)

# API Documentation (Read)

For downloading, we expect to be able to call

```python
# Download files to local folder
success = await ptg_discord.get_messages()
```

and have the output like

```
ptg_discord_data
|--ptg_discord_data.json
|--voice_messages
|----audiofilename123.mp3
|----audiofilename345.ogg
|----audiofilename678.wav
|----audiofilename999.wav
```

and some structured output like

```json
// ptg_discord_data.json
{
    [
        {
            "name": "Len",
            "audio_files": ["audiofilename123.mp3", "audiofile345.ogg"]
        },
        {
            "name": "Raj",
            "audio_files": ["audiofilename678.wav"]
        },
        {
            "name": "Phi",
            "audio_files": ["audiofilename999.ogg"]
        }
    ]
}
```

Internally, we will maintain a map of discord usernames to "prettier" names.

# API Documentation (Write)

```python
# Send message to discord
await ptg_discord.send_podcast(message: str, filename: str)
```

The bot will send some arbitrary message and attach a filename at the specified path (relative to where the script is being run) to discord.
