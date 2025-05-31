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
from openai import OpenAI
import os

class AudioSnippetExtractor:
    def __init__(self, openai_api_key=None):
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model("base")
        
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
        else:
            self.openai_client = None
        
    def transcribe_with_timestamps(self, audio_file):
        """Step 1: Get transcript with word-level timestamps"""
        print(f"Transcribing: {audio_file}")
        
        result = self.whisper_model.transcribe(
            audio_file,
            word_timestamps=True
        )
        
        # Print all segments for debugging
        print("\n--- Whisper Segments ---")
        for i, seg in enumerate(result["segments"]):
            print(f"Segment {i}: {seg['start']:.2f}s - {seg['end']:.2f}s | {seg['text']}")
        print("--- End of Segments ---\n")
        
        return {
            "full_text": result["text"],
            "segments": result["segments"]
        }
    
    def find_interesting_parts(self, transcript):
        """Step 2: Ask LLM to identify interesting segments"""
        
        # Create segments with timestamps for the LLM
        segments_for_llm = []
        for i, segment in enumerate(transcript["segments"]):
            segments_for_llm.append({
                "id": i,
                "text": segment["text"],
                "start": segment["start"],
                "end": segment["end"]
            })
        
        prompt = f"""
You are analyzing an audio transcript to find the most interesting parts for a podcast.

Here are the segments with timestamps:
{json.dumps(segments_for_llm, indent=2)}

You can select interesting moments that may span multiple contiguous segments (for example, from segment 2 to segment 4). For each interesting moment, specify the range of segment IDs it covers, and use the start time of the first segment and the end time of the last segment in the range.

Please identify the 2 most interesting/engaging segments that would make good audio clips.
Look for:
- Funny moments
- Exciting stories
- Emotional moments
- Surprising information

Return ONLY a JSON array like this:
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
            if not self.openai_client:
                raise Exception("No OpenAI client available")
                
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            # Print the raw LLM output for debugging
            print("\n--- Raw OpenAI LLM Output ---")
            print(response.choices[0].message.content)
            print("--- End of LLM Output ---\n")
            
            # Parse the JSON response
            interesting_parts = json.loads(response.choices[0].message.content)
            return interesting_parts
            
        except Exception as e:
            print(f"Error with LLM: {e}")
            # Fallback: return first few segments
            fallback = []
            for i, seg in enumerate(segments_for_llm[:3]):
                fallback.append({
                    "segment_id": i,
                    "reason": "Fallback selection",
                    "start": seg["start"],
                    "end": seg["end"]
                })
            return fallback
    
    def extract_audio_snippets(self, audio_file, interesting_parts, output_folder="snippets"):
        """Step 3: Extract the actual audio clips"""
        
        # Create output folder
        os.makedirs(output_folder, exist_ok=True)
        
        # Load the audio file
        audio = AudioSegment.from_file(audio_file)
        
        snippets = []
        
        for i, part in enumerate(interesting_parts):
            start_ms = part["start"] * 1000  # Convert to milliseconds
            end_ms = part["end"] * 1000
            
            # Extract the snippet
            snippet = audio[start_ms:end_ms]
            
            # Save the snippet
            filename = f"snippet_{i+1}_{part['start']:.1f}s.mp3"
            filepath = os.path.join(output_folder, filename)
            snippet.export(filepath, format="mp3")
            
            snippets.append({
                "filename": filename,
                "filepath": filepath,
                "reason": part["reason"],
                "start": part["start"],
                "end": part["end"],
                "duration": (part["end"] - part["start"])
            })
            
            print(f"✅ Extracted: {filename} ({part['end'] - part['start']:.1f}s) - {part['reason']}")
        
        return snippets
    
    def process_audio_file(self, audio_file, output_folder="snippets"):
        """Main function: Process one audio file and extract interesting snippets"""
        
        print(f"\n🎵 Processing: {audio_file}")
        
        # Step 1: Transcribe
        transcript = self.transcribe_with_timestamps(audio_file)
        
        # Step 2: Find interesting parts
        print("🤖 Asking LLM to find interesting parts...")
        interesting_parts = self.find_interesting_parts(transcript)
        
        print(f"📝 Found {len(interesting_parts)} interesting segments:")
        for part in interesting_parts:
            print(f"  - {part['start']:.1f}s-{part['end']:.1f}s: {part['reason']}")
        
        # Step 3: Extract audio clips
        print("✂️  Extracting audio snippets...")
        snippets = self.extract_audio_snippets(audio_file, interesting_parts, output_folder)
        
        # Save metadata
        metadata = {
            "source_file": audio_file,
            "full_transcript": transcript["full_text"],
            "snippets": snippets
        }
        
        metadata_file = os.path.join(output_folder, "snippets_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"💾 Saved metadata to: {metadata_file}")
        print(f"🎉 Done! Generated {len(snippets)} snippets in '{output_folder}' folder")
        
        return snippets

def main():
    """Simple command line interface"""
    
    if len(sys.argv) < 2:
        print("🎵 Audio Snippet Extractor")
        print("Usage: python snippet_extractor.py <audio_file> [output_folder]")
        print("\nExample: python snippet_extractor.py mike_vacation.wav snippets/")
        return
    
    audio_file = sys.argv[1]
    output_folder = sys.argv[2] if len(sys.argv) > 2 else "snippets"
    
    # Get OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("⚠️  No OPENAI_API_KEY found. Will use fallback snippet selection.")
    
    # Process the audio file
    extractor = AudioSnippetExtractor(openai_key)
    snippets = extractor.process_audio_file(audio_file, output_folder)
    
    print(f"\n📋 Summary:")
    for snippet in snippets:
        print(f"  {snippet['filename']}: {snippet['reason']}")

if __name__ == "__main__":
    import sys
    main()
