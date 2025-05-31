#!/usr/bin/env python3
"""
Simple Podcast Generator
Converts a text script with Speaker: Text format into an audio podcast
"""

import os
import io
import sys
from pathlib import Path
from pydub import AudioSegment
import requests
import json

class SimplePodcastGenerator:
    def __init__(self, elevenlabs_api_key=None, pause_duration=800):
        self.api_key = elevenlabs_api_key
        self.api_url = "https://api.elevenlabs.io/v1"
        self.pause_duration = pause_duration  # milliseconds between speakers
        
        # Default voice IDs (these are ElevenLabs public voices)
        # You can replace these with your own voice IDs
        self.available_voices = [
            "21m00Tcm4TlvDq8ikWAM",  # Rachel - Female
            "AZnzlk1XvdvUeBnXmlld",  # Domi - Female  
            "EXAVITQu4vr4xnSDxMaL",  # Bella - Female
            "ErXwobaYiN019PkySvjV",  # Antoni - Male
            "MF3mGyEYCl7XYWbV9V6O",  # Elli - Female
            "TxGEqnHWrfWFTfGW9XjX",  # Josh - Male
            "VR6AewLTigWG4xSOukaG",  # Arnold - Male
            "pNInz6obpgDQGcFmaJgB",  # Adam - Male
        ]
        
    def parse_script(self, script_text):
        """Parse the simple script format into segments"""
        segments = []
        lines = script_text.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            if ':' in line:
                try:
                    speaker, text = line.split(':', 1)
                    segments.append({
                        'speaker': speaker.strip(),
                        'text': text.strip(),
                        'line': line_num
                    })
                except Exception as e:
                    print(f"Warning: Could not parse line {line_num}: {line}")
                    continue
            else:
                print(f"Warning: Line {line_num} doesn't contain ':' - skipping: {line}")
        
        return segments
    
    def assign_voices(self, segments):
        """Assign voices to speakers"""
        unique_speakers = []
        for seg in segments:
            if seg['speaker'] not in unique_speakers:
                unique_speakers.append(seg['speaker'])
        
        voice_mapping = {}
        for i, speaker in enumerate(unique_speakers):
            voice_id = self.available_voices[i % len(self.available_voices)]
            voice_mapping[speaker] = voice_id
            print(f"Assigned {speaker} -> Voice {i+1}")
        
        return voice_mapping
    
    def text_to_speech(self, text, voice_id):
        """Convert text to speech using ElevenLabs API"""
        if not self.api_key:
            print("Warning: No ElevenLabs API key provided. Using mock audio.")
            # Create a short beep as placeholder
            return AudioSegment.silent(duration=len(text) * 50)  # Rough estimate
        
        url = f"{self.api_url}/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            # Convert audio bytes to AudioSegment
            audio_data = io.BytesIO(response.content)
            return AudioSegment.from_file(audio_data, format="mp3")
            
        except requests.exceptions.RequestException as e:
            print(f"Error generating speech: {e}")
            # Return silent audio as fallback
            return AudioSegment.silent(duration=len(text) * 50)
    
    def generate_podcast(self, script_file_path, output_file="podcast_output.mp3"):
        """Main function to generate podcast from script file"""
        print(f"🎙️  Generating podcast from: {script_file_path}")
        
        # Read script file
        try:
            with open(script_file_path, 'r', encoding='utf-8') as f:
                script_text = f.read()
        except FileNotFoundError:
            print(f"Error: Script file '{script_file_path}' not found!")
            return None
        except Exception as e:
            print(f"Error reading script file: {e}")
            return None
        
        # Parse script
        segments = self.parse_script(script_text)
        if not segments:
            print("Error: No valid segments found in script!")
            return None
        
        print(f"📝 Found {len(segments)} segments")
        
        # Assign voices
        voice_mapping = self.assign_voices(segments)
        
        # Generate audio segments
        audio_segments = []
        
        print("🔊 Generating speech...")
        for i, segment in enumerate(segments, 1):
            print(f"  [{i}/{len(segments)}] {segment['speaker']}: {segment['text'][:50]}...")
            
            # Generate speech
            speech_audio = self.text_to_speech(
                segment['text'], 
                voice_mapping[segment['speaker']]
            )
            
            # Add pause after each segment (except the last one)
            if i < len(segments):
                pause = AudioSegment.silent(duration=self.pause_duration)
                audio_segments.extend([speech_audio, pause])
            else:
                audio_segments.append(speech_audio)
        
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

def create_mock_script():
    """Create a sample script file for testing"""
    mock_script = """Host: Welcome to our weekly friend group update! I'm your host, and this week we heard from Sarah, Mike, and Alex about their adventures.

Sarah: Hey everyone! This week was absolutely amazing. I finally visited that new art museum downtown that everyone's been talking about. The contemporary section was incredible, and I spent like three hours just wandering around. I even bought a print for my apartment!

Host: I love that you stuck with it, Alex! There's something so satisfying about mastering a new skill. That's a wrap for this week's updates, everyone. Thanks for sharing your stories - from art museums to mountain peaks to kitchen adventures, you all know how to make life interesting. We'll be back next week with more updates from the group. Until then, keep living those stories worth sharing!"""
    
    with open("sample_script.txt", "w", encoding="utf-8") as f:
        f.write(mock_script)
    
    print("📄 Created sample_script.txt")
    return "sample_script.txt"

def main():
    """Main function with command line interface"""
    if len(sys.argv) < 2:
        print("🎙️  Podcast Generator")
        print("Usage: python podcast_generator.py <script_file> [output_file]")
        print("\nNo script file provided. Creating a sample script...")
        
        # Create mock script
        script_file = create_mock_script()
        output_file = "sample_podcast.mp3"
    else:
        script_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "podcast_output.mp3"
    
    # Get ElevenLabs API key from environment variable
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("⚠️  No ELEVENLABS_API_KEY environment variable found.")
        print("   The script will run in demo mode with silent audio.")
        print("   To use real voices, set your API key: export ELEVENLABS_API_KEY='your_key_here'")
        print()
    
    # Create generator and process - you can adjust pause duration here
    pause_ms = 5000  # Change this value to adjust pauses (in milliseconds)
    generator = SimplePodcastGenerator(api_key, pause_duration=pause_ms)
    result = generator.generate_podcast(script_file, output_file)
    
    if result:
        print(f"\n🎉 Success! Your podcast is ready: {result}")
    else:
        print("\n❌ Failed to generate podcast")

if __name__ == "__main__":
    main()
