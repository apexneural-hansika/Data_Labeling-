"""
Test script to diagnose audio transcription issues
"""
import os
import sys
import base64
from config import Config
from openai import OpenAI
from agents.content_extractor_agent import ContentExtractorAgent

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

CHECK = "[OK]"
CROSS = "[X]"
WARN = "[!]"

def test_audio_transcription_direct():
    """Test audio transcription using direct OpenAI Whisper API."""
    print_section("Testing Direct OpenAI Whisper API")
    
    openai_key = Config.get_openai_key_for_whisper()
    
    if not openai_key:
        print(f"{CROSS} No OpenAI API key found for Whisper")
        print("   Set OPENAI_DIRECT_API_KEY or OPENAI_API_KEY in .env")
        return False
    
    if openai_key.startswith('sk-or-'):
        print(f"{CROSS} OpenRouter key detected (sk-or-...)")
        print("   Whisper API requires direct OpenAI key (sk-...)")
        return False
    
    print(f"{CHECK} OpenAI key found: {openai_key[:10]}...{openai_key[-4:]}")
    
    # Check if we have a test audio file
    test_files = []
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            ext = os.path.splitext(file)[1].lower()
            if ext in ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.mp4', '.avi', '.mov', '.mkv']:
                test_files.append(os.path.join(uploads_dir, file))
    
    if not test_files:
        print(f"{WARN}  No audio files found in uploads/ directory")
        print("   Please add an audio file to test")
        return None
    
    print(f"{CHECK} Found {len(test_files)} audio file(s)")
    
    # Test with first audio file
    test_file = test_files[0]
    print(f"\n   Testing with: {os.path.basename(test_file)}")
    
    try:
        extractor = ContentExtractorAgent(openai_api_key=openai_key)
        result = extractor.extract_audio(test_file)
        
        if result.get('success'):
            transcript = result.get('raw_text', '')
            print(f"{CHECK} Transcription successful!")
            print(f"   Length: {len(transcript)} characters")
            print(f"   Preview: {transcript[:100]}...")
            return True
        else:
            error = result.get('error', 'Unknown error')
            print(f"{CROSS} Transcription failed: {error}")
            return False
    except Exception as e:
        print(f"{CROSS} Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        return False

def test_audio_with_openrouter():
    """Test audio transcription using OpenRouter with base64-encoded audio."""
    print_section("Testing OpenRouter Audio Transcription (Base64)")
    
    if not Config.USE_OPENROUTER:
        print(f"{WARN}  OpenRouter is not enabled")
        print("   Set USE_OPENROUTER=true in .env to test")
        return None
    
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        print(f"{CROSS} No OpenRouter API key found")
        return False
    
    print(f"{CHECK} OpenRouter key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Check if we have a test audio file
    test_files = []
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            ext = os.path.splitext(file)[1].lower()
            if ext in ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.mp4', '.avi', '.mov', '.mkv']:
                test_files.append(os.path.join(uploads_dir, file))
    
    if not test_files:
        print(f"{WARN}  No audio files found in uploads/ directory")
        print("   Please add an audio file to test")
        return None
    
    test_file = test_files[0]
    print(f"\n   Testing with: {os.path.basename(test_file)}")
    
    try:
        # Read and encode audio file
        with open(test_file, 'rb') as f:
            audio_data = f.read()
        
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Determine MIME type
        ext = os.path.splitext(test_file)[1].lower()
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.flac': 'audio/flac',
            '.m4a': 'audio/mp4',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska'
        }
        mime_type = mime_types.get(ext, 'audio/mpeg')
        
        # Try with openai/whisper-1 through OpenRouter chat completions
        base_url = Config.get_base_url()
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        print(f"   Attempting transcription with openai/whisper-1 via OpenRouter...")
        
        # Note: OpenRouter may not support whisper-1 through chat completions
        # This is a test to see what error we get
        try:
            response = client.chat.completions.create(
                model="openai/whisper-1",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": audio_b64,
                                    "format": mime_type
                                }
                            }
                        ]
                    }
                ]
            )
            print(f"{CHECK} OpenRouter transcription successful!")
            return True
        except Exception as e:
            error_str = str(e)
            print(f"{CROSS} OpenRouter transcription failed: {error_str}")
            
            # Try alternative: Use a model that supports audio through chat completions
            print(f"\n   Trying alternative: openai/gpt-4o with audio input...")
            try:
                response = client.chat.completions.create(
                    model="openai/gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Transcribe this audio file. Return only the transcription text."
                                },
                                {
                                    "type": "input_audio",
                                    "input_audio": {
                                        "data": audio_b64,
                                        "format": mime_type
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=4000
                )
                transcript = response.choices[0].message.content
                print(f"{CHECK} Alternative model (gpt-4o) transcription successful!")
                print(f"   Length: {len(transcript)} characters")
                print(f"   Preview: {transcript[:100]}...")
                return True
            except Exception as e2:
                print(f"{CROSS} Alternative model also failed: {str(e2)}")
                return False
    
    except Exception as e:
        print(f"{CROSS} Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        return False

def main():
    """Run audio transcription tests."""
    print("\n" + "=" * 60)
    print("  AUDIO TRANSCRIPTION DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Test 1: Direct OpenAI Whisper
    result1 = test_audio_transcription_direct()
    
    # Test 2: OpenRouter (if enabled)
    result2 = test_audio_with_openrouter()
    
    # Summary
    print_section("Test Summary")
    
    if result1 is True:
        print(f"{CHECK} Direct OpenAI Whisper: Working")
    elif result1 is False:
        print(f"{CROSS} Direct OpenAI Whisper: Failed")
    else:
        print(f"{WARN}  Direct OpenAI Whisper: Not tested (no audio file)")
    
    if result2 is True:
        print(f"{CHECK} OpenRouter Audio: Working")
    elif result2 is False:
        print(f"{CROSS} OpenRouter Audio: Failed")
    else:
        print(f"{WARN}  OpenRouter Audio: Not tested (OpenRouter disabled or no audio file)")
    
    print("\n[RECOMMENDATIONS]")
    if result1 is False and Config.USE_OPENROUTER:
        print("  - If using OpenRouter, you need a direct OpenAI key for Whisper")
        print("  - Set OPENAI_DIRECT_API_KEY in .env with a direct OpenAI key")
    if result2 is False and Config.USE_OPENROUTER:
        print("  - OpenRouter may not support Whisper API endpoint")
        print("  - Consider using alternative models that support audio via chat completions")
        print("  - Models to try: openai/gpt-4o, anthropic/claude-3.5-sonnet (if supported)")

if __name__ == "__main__":
    main()

