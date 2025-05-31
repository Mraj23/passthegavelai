import os
import json
from typing import List
from pydantic import BaseModel, ValidationError
from openai import AsyncOpenAI
import whisper
import sys
import asyncio
from pydub import AudioSegment
from .create_snippets import AudioSnippetExtractor
from dotenv import load_dotenv
from .get_directory_tree import get_directory_tree

load_dotenv()

# For local execution
# ROOT_DATA_DIR = os.path.join("../data")
ROOT_DATA_DIR = os.path.join("./")

# For local execution
# DOWNLOAD_FOLDER = os.path.join("../", os.getenv("DOWNLOAD_FOLDER"))
# For main execution
DOWNLOAD_FOLDER = os.getenv("DOWNLOAD_FOLDER")

AUDIO_DIR = os.path.join(DOWNLOAD_FOLDER, "voice_messages")
COMBINED_DIR = os.path.join(AUDIO_DIR, "combined")
METADATA_DIR = os.path.join(DOWNLOAD_FOLDER, "ptg_discord_data.json")

# Ensure combined directory exists
os.makedirs(COMBINED_DIR, exist_ok=True)


class ScriptSegment(BaseModel):
    speaker: str
    text: str


class GenerateResponse(BaseModel):
    script: List[ScriptSegment]


class Metadata(BaseModel):
    name: str
    audio_files: List[str]


def get_system_prompt() -> str:
    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("prompt.txt file not found. Please add your system prompt to prompt.txt.")
        sys.exit(1)


def transcribe_audio(audio_path: str) -> str:
    print("transcribing", audio_path)
    try:
        model = whisper.load_model("base")
        result = model.transcribe(audio_path, fp16=False)
        return result["text"]
    except Exception as e:
        print(f"Whisper transcription failed for {audio_path}: {str(e)}")
        return ""


def get_metadata() -> List[Metadata]:
    with open(METADATA_DIR, "r", encoding="utf-8") as f:
        metadata = json.load(f)
        return [Metadata(**data) for data in metadata]


def concat_audio_files(audio_files: List[str], output_path: str):
    """Concatenate multiple audio files into one and export as WAV."""
    combined = AudioSegment.empty()
    for file in audio_files:
        audio = AudioSegment.from_file(file)
        combined += audio
    combined.export(output_path, format="wav")


async def generate_script():
    router_api_key = os.getenv("OPENROUTER_API_KEY")
    if not router_api_key:
        print("OPENROUTER_API_KEY not set in environment.")
        sys.exit(1)
    model = os.getenv("OPENROUTER_MODEL")
    # Process the audio file
    extractor = AudioSnippetExtractor(router_api_key)

    metadata = get_metadata()
    for person in metadata:
        # Concatenate audio files for this person
        input_files = [os.path.join(AUDIO_DIR, f) for f in person.audio_files]
        output_file = os.path.join(COMBINED_DIR, f"{person.name.lower()}.wav")
        concat_audio_files(input_files, output_file)
        person.audio_files = [f"{person.name.lower()}_combined.wav"]

    if not os.path.isdir(AUDIO_DIR):
        print(f"Audio directory not found: {AUDIO_DIR}")
        sys.exit(1)

    audio_files = [
        f
        for f in os.listdir(COMBINED_DIR)
        if os.path.isfile(os.path.join(COMBINED_DIR, f))
    ]
    if not audio_files:
        print(f"No audio files found in {COMBINED_DIR}")
        sys.exit(1)

    transcripts = {}
    for audio_file in audio_files:
        audio_path = os.path.join(COMBINED_DIR, audio_file)
        snippets = await extractor.process_audio_file(
            audio_path, os.path.join(ROOT_DATA_DIR, "snippets")
        )
        print(snippets)

        transcript = transcribe_audio(audio_path)
        transcripts[audio_file] = transcript

    snippets_tree = get_directory_tree("./snippet")

    system_prompt = get_system_prompt()
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=router_api_key,
    )
    user_prompt = json.dumps(
        {"transcripts": transcripts, "snippets_tree": snippets_tree}
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        content = response.choices[0].message.content.strip()
        script_json = json.loads(content)

        with open(
            os.path.join(ROOT_DATA_DIR, "transcript.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(script_json, f, indent=2, ensure_ascii=False)

        print(json.dumps(json.loads(script_json), indent=2, ensure_ascii=False))

    except (json.JSONDecodeError, ValidationError) as e:
        print(
            f"Failed to parse model output as valid JSON: {str(e)}\nRaw output: {content}"
        )
        sys.exit(1)
    except Exception as e:
        print(f"OpenRouter API error: {str(e)}")
        sys.exit(1)


def generate_script_sync():
    asyncio.run(generate_script())


if __name__ == "__main__":
    asyncio.run(generate_script())
