# Pass The Gavel

Len, Raj, Phi project for CMU T&E Home-cooked Apps AI Hackathon

# About 

Pass The Gavel is a project we built to help friend groups or families stay connected by automatically turning their shared voice messages into short, entertaining podcast episodes.

How it works:
- Collects Voice Messages: The system connects to a Discord server, downloads recent voice messages from users, and organizes them by sender.
- Generates Highlights & Transcript: Using speech-to-text (Whisper) and an LLM (via OpenRouter), it transcribes the audio, identifies the most interesting or funny moments, and generates a podcast script. The script is structured as a conversation between two hosts, with audio snippets from the friends’ messages inserted at relevant points.
- Creates a Podcast: The script and audio snippets are combined using text-to-speech (via ElevenLabs) and audio processing to produce a seamless podcast episode.
- Sends Podcast Back to Discord: The finished podcast audio file is automatically sent back to a Discord channel for everyone to listen to.

# Setup

## Python Commands

```bash
# Start environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

### Pre-commit Integration

The pre-commit hook will also run flake8 automatically on staged files along with black.

# Install requirements

pip install -r requirements.txt

# Save new requirements
pip freeze > requirements.txt

# Install git hook scripts
pre-commit install

# Run pre-commit
pre-commit run -a
```

## Manual Run

You can do manually to

```bash
flake8 .

black .
```

## Pre-commit Formatting

This project uses [pre-commit](https://pre-commit.com/) to run code formatting checks before commits.

1. Install pre-commit if you haven't already:

```bash
pip install pre-commit
```

2. Install the git hook scripts:

```bash
pre-commit install
```

3. Now, every time you commit, `black` will automatically format your Python code according to the configuration in `pyproject.toml`.

## Manual Formatting

You can also manually run black on the entire codebase with:

```bash
black .
```
