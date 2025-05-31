#!/usr/bin/env python3
"""
Simple Podcast Generator
Converts a text script with Speaker: Text format into an audio podcast
"""

import os
import io
import sys
import json
from pathlib import Path
from pydub import AudioSegment
import requests
import datetime


class SimplePodcastGenerator:
    def __init__(self, elevenlabs_api_key=None, pause_duration=800):
        self.api_key = elevenlabs_api_key
        self.api_url = "https://api.elevenlabs.io/v1"
        self.pause_duration = pause_duration  # milliseconds between speakers
        # Default voice IDs (these are ElevenLabs public voices)
        # You can replace these with your own voice IDs
        self.available_voices = [
            "21m00Tcm4TlvDq8ikWAM",  # Rachel - Female
            "ErXwobaYiN019PkySvjV",  # Antoni - Male
            "TxGEqnHWrfWFTfGW9XjX",  # Josh - Male
            "VR6AewLTigWG4xSOukaG",  # Arnold - Male
            "pNInz6obpgDQGcFmaJgB",  # Adam - Male
        ]

    def load_json_script(self, json_file_path):
        """Load segments from JSON file"""
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")

        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                segments = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {json_file_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error reading JSON file {json_file_path}: {e}")

        if not isinstance(segments, list):
            raise ValueError("JSON file must contain an array of segments")

        if not segments:
            raise ValueError("JSON file contains no segments")

        print(f"📝 Loaded {len(segments)} segments from JSON")

        # Validate and categorize segments
        for i, segment in enumerate(segments):
            if not isinstance(segment, dict):
                raise ValueError(f"Segment {i} must be an object, got: {type(segment)}")

            if "speaker" in segment and "text" in segment:
                if not segment["speaker"].strip():
                    raise ValueError(f"Segment {i}: Speaker name cannot be empty")
                if not segment["text"].strip():
                    raise ValueError(f"Segment {i}: Text cannot be empty")
                segment["type"] = "speech"

            elif "snippet" in segment:
                if not segment["snippet"].strip():
                    raise ValueError(f"Segment {i}: Snippet path cannot be empty")
                segment["type"] = "audio_file"

            else:
                raise ValueError(
                    f"Segment {i} must have either 'speaker'+'text' OR 'snippet' fields. Got: {list(segment.keys())}"
                )

        return segments

    def assign_voices(self, segments):
        """Assign voices to speakers"""
        unique_speakers = []
        for seg in segments:
            if "speaker" in seg and seg["speaker"] not in unique_speakers:
                unique_speakers.append(seg["speaker"])

        voice_mapping = {}
        for i, speaker in enumerate(unique_speakers):
            voice_id = self.available_voices[i % len(self.available_voices)]
            voice_mapping[speaker] = voice_id
            print(f"Assigned {speaker} -> Voice {i+1}")

        return voice_mapping

    def text_to_speech(self, text, voice_id):
        """Convert text to speech using ElevenLabs API"""
        if not self.api_key:
            raise ValueError(
                "ElevenLabs API key is required for text-to-speech generation. Set ELEVENLABS_API_KEY environment variable."
            )

        url = f"{self.api_url}/text-to-speech/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }

        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            # Convert audio bytes to AudioSegment
            audio_data = io.BytesIO(response.content)
            return AudioSegment.from_file(audio_data, format="mp3")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Failed to generate speech for text: '{text[:50]}...'. ElevenLabs API error: {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error during text-to-speech conversion: {e}"
            )

    def generate_podcast(self, json_file_path, output_file="podcast_output.mp3"):
        """Main function to generate podcast from JSON file"""
        print(f"🎙️  Generating podcast from: {json_file_path}")

        # Load segments from JSON
        segments = self.load_json_script(json_file_path)
        if not segments:
            print("Error: No valid segments found in JSON file!")
            return None

        print(f"📝 Found {len(segments)} segments")

        # Assign voices to speakers
        voice_mapping = self.assign_voices(segments)

        # Generate audio segments
        audio_segments = []

        print("🔊 Generating podcast...")
        for i, segment in enumerate(segments, 1):
            if segment.get("type") == "speech":
                print(
                    f"  [{i}/{len(segments)}] 🗣️  {segment['speaker']}: {segment['text'][:50]}..."
                )

                # Generate speech
                speech_audio = self.text_to_speech(
                    segment["text"], voice_mapping[segment["speaker"]]
                )
                audio_segments.append(speech_audio)

            elif segment.get("type") == "audio_file":
                print(
                    f"  [{i}/{len(segments)}] 🎵 Loading audio file: {segment['snippet']}"
                )

                try:
                    # Load the audio file
                    audio_file = AudioSegment.from_file(segment["snippet"])
                    audio_segments.append(audio_file)
                    print(f"    ✅ Added {len(audio_file)/1000:.1f}s audio clip")
                except Exception as e:
                    print(f"    ❌ Error loading {segment['snippet']}: {e}")
                    # Add silence as fallback
                    audio_segments.append(AudioSegment.silent(duration=2000))

            # Add pause between segments (except the last one)
            if i < len(segments):
                pause = AudioSegment.silent(duration=self.pause_duration)
                audio_segments.append(pause)

        # Combine all segments
        print("🎵 Combining audio segments...")
        if audio_segments:
            final_podcast = sum(audio_segments)

            # Normalize audio levels
            final_podcast = final_podcast.normalize()

            # Export
            print(f"💾 Exporting to: {output_file}")
            final_podcast.export(output_file, format="mp3", bitrate="192k")

            duration = len(final_podcast) / 1000  # Convert to seconds
            print(f"✅ Podcast generated successfully!")
            print(f"   Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            print(f"   File: {output_file}")

            return output_file
        else:
            print("Error: No audio segments generated!")
            return None


def generate_podcast_from_data():
    input_file = "data/transcript.json"
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = f"data/podcast_{today}.mp3"

    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("⚠️  No ELEVENLABS_API_KEY found in config.")
        raise EnvironmentError("ELEVENLABS_API_KEY is required.")

    pause_ms = 200
    generator = SimplePodcastGenerator(api_key, pause_duration=pause_ms)
    result = generator.generate_podcast(input_file, output_file)

    if result:
        print(f"\n🎉 Success! Your podcast is ready: {result}")
    else:
        print("\n❌ Failed to generate podcast")
    return output_file

def main():
    input_file = "data/transcript.json"
    output_file = f"data/podcast_today.mp3"

    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("⚠️  No ELEVENLABS_API_KEY environment variable found.")
        raise EnvironmentError("ELEVENLABS_API_KEY environment variable is missing.")
    
    # Create generator and process - you can adjust pause duration here
    pause_ms = 800  # Change this value to adjust pauses (in milliseconds)
    generator = SimplePodcastGenerator(api_key, pause_duration=pause_ms)
    result = generator.generate_podcast(input_file, output_file)
    
    if result:
        print(f"\n🎉 Success! Your podcast is ready: {result}")
    else:
        print("\n❌ Failed to generate podcast")
    return output_file


if __name__ == "__main__":
    main()
