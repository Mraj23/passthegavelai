import os
import json
from typing import List, Dict
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
from openai import AsyncOpenAI
import whisper
import tempfile
import sys
import asyncio
from pydub import AudioSegment
from create_snippets import AudioSnippetExtractor

load_dotenv()


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
    with open("./audio/metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)["metadata"]
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
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
    # Process the audio file
    extractor = AudioSnippetExtractor(router_api_key)

    metadata = get_metadata()
    for person in metadata:
        # Concatenate audio files for this person
        input_files = [os.path.join("audio", f) for f in person.audio_files]
        output_file = os.path.join("audio", f"{person.name.lower()}_combined.wav")
        concat_audio_files(input_files, output_file)
        person.audio_files = [f"{person.name.lower()}_combined.wav"]
    
    audio_dir = "audio"
    if not os.path.isdir(audio_dir):
        print(f"Audio directory not found: {audio_dir}")
        sys.exit(1)
    audio_files = [f for f in os.listdir(audio_dir) if os.path.isfile(os.path.join(audio_dir, f)) and f.lower().endswith("_combined.wav")]
    if not audio_files:
        print(f"No audio files found in {audio_dir}")
        sys.exit(1)
    
    
    transcripts = {}
    for audio_file in audio_files:
        audio_path = os.path.join(audio_dir, audio_file) 
        snippets = await extractor.process_audio_file(audio_path, "snippet")
       
        transcript = transcribe_audio(audio_path)
        transcripts[audio_file] = transcript

    system_prompt = get_system_prompt()
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=router_api_key,
    )
    user_prompt = json.dumps(transcripts)    
    
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        content = response.choices[0].message.content.strip()
        script_json = json.loads(content)
        validated = GenerateResponse(script=[ScriptSegment(**seg) for seg in script_json])
        print(json.dumps(json.loads(validated.json()), indent=2, ensure_ascii=False))
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Failed to parse model output as valid JSON: {str(e)}\nRaw output: {content}")
        sys.exit(1)
    except Exception as e:
        print(f"OpenRouter API error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(generate_script())
