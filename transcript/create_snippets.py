#!/usr/bin/env python3
"""
Simple Audio Snippet Extractor
1. Transcribe audio with timestamps using Whisper
2. Ask LLM to find interesting parts
3. Extract those parts as audio snippets
"""

import whisper
import json
from pydub import AudioSegment
from openai import AsyncOpenAI
import os
import re
import asyncio


class AudioSnippetExtractor:
    def __init__(self, router_api_key=None):
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model("base")
        self.openrouter_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=router_api_key,
        )
        self.model = os.getenv("OPENROUTER_MODEL")

    def transcribe_with_timestamps(self, audio_file):
        """Step 1: Get transcript with word-level timestamps"""
        print(f"Transcribing: {audio_file}")

        result = self.whisper_model.transcribe(
            audio_file, word_timestamps=True, fp16=False
        )

        # Print all segments for debugging
        print("\n--- Whisper Segments ---")
        for i, seg in enumerate(result["segments"]):
            print(
                f"Segment {i}: {seg['start']:.2f}s - {seg['end']:.2f}s | {seg['text']}"
            )
        print("--- End of Segments ---\n")

        return {"full_text": result["text"], "segments": result["segments"]}

    async def find_interesting_parts(self, transcript):
        """Step 2: Ask LLM to identify interesting segments"""

        # Create segments with timestamps for the LLM
        segments_for_llm = []
        for i, segment in enumerate(transcript["segments"]):
            segments_for_llm.append(
                {
                    "id": i,
                    "text": segment["text"],
                    "start": segment["start"],
                    "end": segment["end"],
                }
            )

        prompt = f"""
You are analyzing an audio transcript to find the most interesting parts for a podcast about a group of friends. Each transcript is going to be about a persons life updates and what they did over the week or month.

Here are the segments with timestamps:
{json.dumps(segments_for_llm, indent=2)}

You can select interesting moments that may span multiple contiguous segments (for example, from segment 2 to segment 4). For each interesting moment, specify the range of segment IDs it covers, and use the start time of the first segment and the end time of the last segment in the range.

Please identify the 2 most interesting/engaging segments that would make good audio clips.
Look for:
- Really Funny moments
- Big life updates

Return ONLY a JSON array like this. Do NOT include backticks (`):
[
  {{
    "segment_start_id": 2,
    "segment_end_id": 4,
    "reason": "Funny story about cooking disaster",
    "start": 15.2,   // start time of segment 2
    "end": 28.7      // end time of segment 4
  }},
  {{
    "segment_start_id": 5,
    "segment_end_id": 6,
    "reason": "Exciting hiking adventure",
    "start": 45.1,   // start time of segment 5
    "end": 52.3      // end time of segment 6
  }}
]
"""

        try:
            if not self.openrouter_client:
                raise Exception("No OpenRouter client available")

            response = await self.openrouter_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            # Print the raw LLM output for debugging
            print("\n--- Raw OpenRouter LLM Output ---")
            content = response.choices[0].message.content.strip()
            print(content)
            print("--- End of LLM Output ---\n")

            # Parse the JSON response
            interesting_parts = json.loads(response.choices[0].message.content)
            return interesting_parts

        except Exception as e:
            print(f"Error with LLM: {e}")
            # Fallback: return first few segments
            fallback = []
            for i, seg in enumerate(segments_for_llm[:3]):
                fallback.append(
                    {
                        "segment_id": i,
                        "reason": "Fallback selection",
                        "start": seg["start"],
                        "end": seg["end"],
                    }
                )
            return fallback

    def sanitize_filename(self, text):
        # Lowercase, replace spaces with underscores, remove non-alphanumeric/underscore
        return re.sub(r"[^a-zA-Z0-9_]", "", text.replace(" ", "_")).lower()

    def extract_audio_snippets(
        self, audio_file, interesting_parts, output_folder="snippets"
    ):
        """Step 3: Extract the actual audio clips"""

        # Create a subfolder for this audio file
        audio_base = os.path.splitext(os.path.basename(audio_file))[0]
        audio_output_folder = os.path.join(output_folder, audio_base)
        os.makedirs(audio_output_folder, exist_ok=True)

        # Load the audio file
        audio = AudioSegment.from_file(audio_file)

        snippets = []

        for i, part in enumerate(interesting_parts):
            start_ms = part["start"] * 1000  # Convert to milliseconds
            end_ms = part["end"] * 1000

            # Extract the snippet
            snippet = audio[start_ms:end_ms]

            # Sanitize reason for filename
            reason_safe = self.sanitize_filename(part["reason"])
            filename = f"{i+1}_{reason_safe}.mp3"
            filepath = os.path.join(audio_output_folder, filename)
            snippet.export(filepath, format="mp3")

            snippets.append(
                {
                    "filename": filename,
                    "filepath": filepath,
                    "reason": part["reason"],
                    "start": part["start"],
                    "end": part["end"],
                    "duration": (part["end"] - part["start"]),
                }
            )

            print(
                f"✅ Extracted: {filename} ({part['end'] - part['start']:.1f}s) - {part['reason']}"
            )

        return snippets

    async def process_audio_file(self, audio_file, output_folder="snippets"):
        """Main function: Process one audio file and extract interesting snippets"""

        print(f"\n🎵 Processing: {audio_file}")

        # Step 1: Transcribe
        transcript = self.transcribe_with_timestamps(audio_file)

        # Step 2: Find interesting parts
        print("🤖 Asking LLM to find interesting parts...")
        interesting_parts = await self.find_interesting_parts(transcript)

        print(f"📝 Found {len(interesting_parts)} interesting segments:")
        for part in interesting_parts:
            print(f"  - {part['start']:.1f}s-{part['end']:.1f}s: {part['reason']}")

        # Step 3: Extract audio clips
        print("✂️  Extracting audio snippets...")
        snippets = self.extract_audio_snippets(
            audio_file, interesting_parts, output_folder
        )

        # Save metadata
        audio_base = os.path.splitext(os.path.basename(audio_file))[0]
        audio_output_folder = os.path.join(output_folder, audio_base)
        metadata = {
            "source_file": audio_file,
            "full_transcript": transcript["full_text"],
            "snippets": snippets,
        }

        # metadata_file = os.path.join(audio_output_folder, "snippets_metadata.json")
        # with open(metadata_file, 'w') as f:
        #     json.dump(metadata, f, indent=2)
        # print(f"💾 Saved metadata to: {metadata_file}")

        print(f"🎉 Done! Generated {len(snippets)} snippets in '{audio_output_folder}' folder")

        return snippets


def main():
    """Simple command line interface"""

    if len(sys.argv) < 2:
        print("🎵 Audio Snippet Extractor")
        print("Usage: python create_snippets.py <audio_file> [output_folder]")
        print("\nExample: python create_snippets.py mike_vacation.wav snippets/")
        return

    audio_file = sys.argv[1]
    output_folder = sys.argv[2] if len(sys.argv) > 2 else "snippets"

    # Get OpenRouter API key
    router_api_key = os.getenv("OPENROUTER_API_KEY")
    if not router_api_key:
        print("⚠️  No OPENROUTER_API_KEY found. Will use fallback snippet selection.")
        openrouter_client = None
    else:
        openrouter_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=router_api_key,
        )

    # Process the audio file
    extractor = AudioSnippetExtractor(openrouter_client)
    asyncio.run(extractor.process_audio_file(audio_file, output_folder))


if __name__ == "__main__":
    import sys

    main()
