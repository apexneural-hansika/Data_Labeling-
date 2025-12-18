"""
Test actual audio transcription with the content extractor agent
"""
import os
import sys
from config import Config
from agents.content_extractor_agent import ContentExtractorAgent

def main():
    print("\n" + "=" * 60)
    print("  TESTING ACTUAL AUDIO TRANSCRIPTION")
    print("=" * 60)
    
    # Find audio file
    uploads_dir = "uploads"
    audio_file = None
    
    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            ext = os.path.splitext(file)[1].lower()
            if ext in ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.mp4', '.avi', '.mov', '.mkv']:
                audio_file = os.path.join(uploads_dir, file)
                break
    
    if not audio_file:
        print("[ERROR] No audio file found in uploads/ directory")
        sys.exit(1)
    
    print(f"\n[INFO] Testing with: {os.path.basename(audio_file)}")
    print(f"[INFO] File size: {os.path.getsize(audio_file) / 1024:.2f} KB")
    
    # Initialize content extractor
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found")
        sys.exit(1)
    
    print(f"[INFO] Using API key: {api_key[:10]}...{api_key[-4:]}")
    print(f"[INFO] Using OpenRouter: {Config.USE_OPENROUTER}")
    
    extractor = ContentExtractorAgent(openai_api_key=api_key)
    
    print("\n[INFO] Starting transcription...")
    print("-" * 60)
    
    try:
        result = extractor.extract_audio(audio_file)
        
        print("\n" + "=" * 60)
        print("  TRANSCRIPTION RESULT")
        print("=" * 60)
        
        if result.get('success'):
            transcript = result.get('raw_text', '')
            print(f"\n[SUCCESS] Transcription completed!")
            print(f"[INFO] Method: {result.get('extraction_method', 'unknown')}")
            print(f"[INFO] Length: {len(transcript)} characters")
            print(f"[INFO] Word count: {len(transcript.split())} words")
            print("\n" + "-" * 60)
            print("TRANSCRIPT:")
            print("-" * 60)
            print(transcript)
            print("-" * 60)
        else:
            error = result.get('error', 'Unknown error')
            error_type = result.get('error_type', 'unknown')
            print(f"\n[FAILED] Transcription failed!")
            print(f"[ERROR] {error}")
            print(f"[ERROR TYPE] {error_type}")
            
            if 'OPENAI_DIRECT_API_KEY' in error:
                print("\n[RECOMMENDATION] Set OPENAI_DIRECT_API_KEY in .env file")
        
    except Exception as e:
        print(f"\n[EXCEPTION] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

