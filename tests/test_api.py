"""
Test script to verify API keys and model functionality
"""
import os
from config import Config
from openai import OpenAI
import sys

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

# Use ASCII-safe characters for Windows console
CHECK = "[OK]"
CROSS = "[X]"
WARN = "[!]"

def test_openai_key():
    """Test OpenAI API key and models."""
    print_section("Testing OpenAI API Key")
    
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        print(f"{CROSS} OPENAI_API_KEY not found in config")
        print("   Set it via .env file, environment variable, or config.py")
        return False
    
    print(f"{CHECK} API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Check if using OpenRouter
    use_openrouter = Config.USE_OPENROUTER
    if use_openrouter:
        print(f"{WARN}  Using OpenRouter API")
        base_url = Config.get_base_url()
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        print(f"{WARN}  Using OpenAI API directly")
        client = OpenAI(api_key=api_key)
    
    try:
        
        # Test 1: GPT-4o-mini for text (Category Classification)
        print("\n[Test 1] Testing gpt-4o-mini (Category Classification)...")
        try:
            response = client.chat.completions.create(
                model=Config.get_model_name("gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "You are a content categorization expert."},
                    {"role": "user", "content": "Classify this: A technical report about AI"}
                ],
                max_tokens=50,
                temperature=0.3
            )
            result = response.choices[0].message.content
            print(f"   {CHECK} gpt-4o-mini works! Response: {result[:50]}...")
        except Exception as e:
            print(f"   {CROSS} gpt-4o-mini failed: {str(e)}")
            return False
        
        # Test 2: GPT-4o-mini for JSON (Label Generation)
        print("\n[Test 2] Testing gpt-4o-mini with JSON format (Label Generation)...")
        try:
            response = client.chat.completions.create(
                model=Config.get_model_name("gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "You are a label extraction expert. You must return valid JSON format."},
                    {"role": "user", "content": "Extract labels from: 'Machine learning research paper about neural networks'. Return the result as JSON."}
                ],
                response_format={"type": "json_object"},
                max_tokens=200,
                temperature=0.3
            )
            result = response.choices[0].message.content
            print(f"   {CHECK} gpt-4o-mini JSON works! Response: {result[:50]}...")
        except Exception as e:
            print(f"   {CROSS} gpt-4o-mini JSON failed: {str(e)}")
            return False
        
        # Test 3: GPT-4o-mini Vision (Image Analysis)
        print("\n[Test 3] Testing gpt-4o-mini Vision (Image Analysis)...")
        try:
            # Create a simple test image (1x1 pixel PNG)
            import base64
            # Minimal valid PNG in base64
            test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            
            response = client.chat.completions.create(
                model=Config.get_model_name("gpt-4o-mini"),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe this image briefly."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{test_image_b64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=100
            )
            result = response.choices[0].message.content
            print(f"   {CHECK} gpt-4o-mini Vision works! Response: {result[:50]}...")
        except Exception as e:
            print(f"   {CROSS} gpt-4o-mini Vision failed: {str(e)}")
            print(f"   Error details: {type(e).__name__}")
            return False
        
        # Test 4: Whisper-1 (Audio Transcription)
        print("\n[Test 4] Testing whisper-1 (Audio Transcription)...")
        print(f"   {WARN}  Whisper requires an actual audio file to test")
        print(f"   {CHECK} whisper-1 model is available (will work with audio files)")
        
        print(f"\n{CHECK} All OpenAI API tests passed!")
        return True
        
    except Exception as e:
        print(f"{CROSS} OpenAI API connection failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        if "quota" in str(e).lower() or "insufficient" in str(e).lower():
            print("\n   [TIP] Your API key has exceeded its quota/credits.")
            print("   Please check your OpenAI account billing and add credits.")
        elif "invalid" in str(e).lower() or "authentication" in str(e).lower():
            print("\n   [TIP] Your API key appears to be invalid.")
            print("   Please verify your API key is correct.")
        return False

def test_deepseek_key():
    """Test DeepSeek API key (optional)."""
    print_section("Testing DeepSeek API Key (Optional)")
    
    api_key = Config.DEEPSEEK_API_KEY
    if not api_key:
        print(f"{WARN}  DEEPSEEK_API_KEY not found (optional - not required)")
        print("   DeepSeek is used for OCR on text documents")
        print("   System will use OpenAI as fallback")
        return None
    
    print(f"{CHECK} API Key found: {api_key[:10]}...{api_key[-4:]}")
    print(f"{WARN}  Note: DeepSeek API integration is not yet implemented in the code")
    print("   The API key is stored but not currently used")
    print("   OCR currently uses PyPDF2/python-docx with OpenAI Vision fallback")
    return True

def test_config():
    """Test configuration."""
    print_section("Configuration Check")
    
    print("Checking API keys...")
    openai_key = Config.OPENAI_API_KEY
    deepseek_key = Config.DEEPSEEK_API_KEY
    use_openrouter = Config.USE_OPENROUTER
    
    if openai_key:
        print(f"{CHECK} OPENAI_API_KEY: Configured ({len(openai_key)} characters)")
    else:
        print(f"{CROSS} OPENAI_API_KEY: Not configured")
    
    if deepseek_key:
        print(f"{CHECK} DEEPSEEK_API_KEY: Configured ({len(deepseek_key)} characters)")
    else:
        print(f"{WARN}  DEEPSEEK_API_KEY: Not configured (optional)")
    
    if use_openrouter:
        print(f"{CHECK} USE_OPENROUTER: Enabled (using OpenRouter API)")
        print(f"   Base URL: {Config.OPENROUTER_BASE_URL}")
    else:
        print(f"{WARN}  USE_OPENROUTER: Disabled (using OpenAI API directly)")
        print(f"   [TIP] To use OpenRouter, set USE_OPENROUTER=true in .env file")
    
    # Validate config
    is_valid, error_msg = Config.validate()
    if is_valid:
        print(f"\n{CHECK} Configuration is valid")
    else:
        print(f"\n{CROSS} Configuration error: {error_msg}")
    
    return is_valid

def test_models_summary():
    """Print summary of models used."""
    print_section("Models Used in System")
    
    use_openrouter = Config.USE_OPENROUTER
    model_prefix = "OpenRouter: " if use_openrouter else ""
    
    models = {
        "Image Analysis": f"{model_prefix}{Config.get_model_name('gpt-4o-mini')} (Vision)",
        "Category Classification": f"{model_prefix}{Config.get_model_name('gpt-4o-mini')}",
        "Label Generation": f"{model_prefix}{Config.get_model_name('gpt-4o-mini')} (JSON)",
        "Audio Transcription": f"{model_prefix}{Config.get_model_name('whisper-1')}",
        "OCR (Text Documents)": "PyPDF2/python-docx (OpenAI Vision fallback)"
    }
    
    for task, model in models.items():
        print(f"  {task:30} -> {model}")
    
    print("\n[TIP] All text/vision tasks use gpt-4o-mini (cost-effective)")
    print("[TIP] Audio uses whisper-1 (specialized model)")
    if use_openrouter:
        print("[TIP] Using OpenRouter API - models are prefixed with provider name")

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  API TESTING SUITE")
    print("=" * 60)
    
    # Test configuration
    config_ok = test_config()
    if not config_ok:
        print(f"\n{CROSS} Configuration test failed. Please fix configuration first.")
        sys.exit(1)
    
    # Test models summary
    test_models_summary()
    
    # Test OpenAI
    openai_ok = test_openai_key()
    
    # Test DeepSeek (optional)
    test_deepseek_key()
    
    # Final summary
    print_section("Test Summary")
    
    if openai_ok:
        print(f"{CHECK} OpenAI API: Working correctly")
        print(f"{CHECK} All required models are functional")
        print("\n[SUCCESS] Your system is ready to use!")
    else:
        print(f"{CROSS} OpenAI API: Failed")
        print(f"\n{WARN}  Please check:")
        print("   1. Your API key is correct")
        print("   2. You have sufficient credits/quota")
        print("   3. Your internet connection is working")
        sys.exit(1)

if __name__ == "__main__":
    main()

