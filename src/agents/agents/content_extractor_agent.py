"""
Content Extractor Agent - Extracts content based on modality
- Text documents: DeepSeek OCR (via API)
- Audio: Whisper transcription
- Images: Visual description (NO OCR)
"""
import os
import sys
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from openai import OpenAI
import io

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config import Config
from utils.api_utils import retry_with_backoff, handle_api_error
from utils.logger import get_system_logger

logger = get_system_logger()


class ContentExtractorAgent:
    """Extracts content from different file modalities."""
    
    def __init__(self, deepseek_api_key: Optional[str] = None, openai_api_key: Optional[str] = None):
        """
        Initialize the content extractor.
        
        Args:
            deepseek_api_key: API key for DeepSeek OCR (optional, can use OpenAI as fallback)
            openai_api_key: API key for OpenAI/OpenRouter (for Whisper and image descriptions)
        """
        self.deepseek_api_key = deepseek_api_key
        if openai_api_key:
            base_url = Config.get_base_url()
            self.openai_client = OpenAI(
                api_key=openai_api_key,
                base_url=base_url
            ) if base_url else OpenAI(api_key=openai_api_key)
        else:
            self.openai_client = None
    
    def extract_text_document(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from document using OCR.
        
        Args:
            file_path: Path to the text document
            
        Returns:
            Dictionary with extracted text
        """
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # For PDF, TXT, DOCX, CSV - use appropriate extraction
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.txt':
                # Simple text file
                raw_text = file_content.decode('utf-8', errors='ignore')
            elif file_ext == '.csv':
                # CSV file
                raw_text = file_content.decode('utf-8', errors='ignore')
            elif file_ext == '.pdf':
                # PDF - use OCR via API
                raw_text = self._extract_pdf_ocr(file_content)
            elif file_ext in ['.docx', '.doc']:
                # Word document - use OCR via API
                raw_text = self._extract_docx_ocr(file_content)
            else:
                raw_text = file_content.decode('utf-8', errors='ignore')
            
            return {
                'raw_text': raw_text,
                'extraction_method': 'ocr' if file_ext in ['.pdf', '.docx', '.doc'] else 'direct',
                'success': True
            }
        except Exception as e:
            return {
                'raw_text': '',
                'extraction_method': 'failed',
                'success': False,
                'error': str(e)
            }
    
    def extract_audio(self, file_path: str) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary with transcribed text
        """
        try:
            if not self.openai_client:
                return {
                    'raw_text': '',
                    'success': False,
                    'error': 'OpenAI API key not provided'
                }
            
            # Transcribe using Whisper with retry logic
            transcript = self._transcribe_audio(file_path)
            
            return {
                'raw_text': transcript,
                'extraction_method': 'whisper',
                'success': True
            }
        except Exception as e:
            error_info = handle_api_error(e)
            print(f"[Content Extractor] Audio transcription error: {e} (Type: {error_info['error_type']})")
            return {
                'raw_text': '',
                'success': False,
                'error': str(e),
                'error_type': error_info['error_type']
            }
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _transcribe_audio(self, file_path: str) -> str:
        """Transcribe audio file with retry logic and fallback support."""
        filename = os.path.basename(file_path)
        
        # Strategy 1: Try direct OpenAI Whisper API (best quality, fastest)
        openai_key = Config.get_openai_key_for_whisper()
        
        if openai_key and not openai_key.startswith('sk-or-'):
            # We have a direct OpenAI key, try Whisper API first
            try:
                return self._transcribe_with_whisper_api(file_path, filename, openai_key)
            except Exception as e:
                print(f"[Audio] Whisper API failed: {e}. Trying fallback...")
                # Continue to fallback methods
        
        # Strategy 2: If using OpenRouter, try audio-capable models via chat completions
        if Config.USE_OPENROUTER and self.openai_client:
            try:
                return self._transcribe_with_openrouter_audio(file_path, filename)
            except Exception as e:
                print(f"[Audio] OpenRouter audio transcription failed: {e}")
                # Continue to final fallback
        
        # Strategy 3: Final fallback - raise error with helpful message
        if Config.USE_OPENROUTER:
            raise ValueError(
                "Audio transcription failed. Options:\n"
                "1. Set OPENAI_DIRECT_API_KEY with a direct OpenAI key for Whisper API\n"
                "2. Use a model that supports audio via OpenRouter (e.g., openai/gpt-4o)\n"
                "Current OpenRouter key cannot access Whisper API endpoint."
            )
        else:
            raise ValueError(
                "OpenAI API key required for Whisper transcription. "
                "Please set OPENAI_API_KEY or OPENAI_DIRECT_API_KEY."
            )
    
    def _transcribe_with_whisper_api(self, file_path: str, filename: str, api_key: str) -> str:
        """Transcribe using direct OpenAI Whisper API."""
        from openai import OpenAI as OpenAI_Direct
        whisper_client = OpenAI_Direct(api_key=api_key)
        
        # Read file content into BytesIO for proper handling
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Create a BytesIO object from the file content
        audio_file = io.BytesIO(file_content)
        audio_file.name = filename  # Set filename attribute
        
        # Whisper API always uses "whisper-1" model name
        transcript = whisper_client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, audio_file, self._get_mime_type(filename)),
            response_format="text"
        )
        return transcript
    
    def _transcribe_with_openrouter_audio(self, file_path: str, filename: str) -> str:
        """Transcribe using OpenRouter with audio-capable models via chat completions."""
        # Read and encode audio file
        with open(file_path, 'rb') as f:
            audio_data = f.read()
        
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        mime_type = self._get_mime_type(filename)
        
        # Try models in order of preference (models that support audio input)
        # Note: Voxtral is specifically designed for audio transcription
        fallback_models = [
            "mistralai/voxtral-small-24b-2507",  # Voxtral Small - designed for audio transcription
            "openai/gpt-4o",                     # GPT-4o (fallback, may not work)
            "openai/gpt-4o-mini",                # GPT-4o-mini (fallback, may not work)
        ]
        
        last_error = None
        for model in fallback_models:
            # Try different audio input formats based on OpenAI/OpenRouter specs
            audio_formats = [
                # Format 1: OpenAI GPT-4o format with input_audio object
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": audio_b64,
                        "format": mime_type
                    }
                },
                # Format 2: Data URL format
                {
                    "type": "input_audio",
                    "input_audio": f"data:{mime_type};base64,{audio_b64}"
                },
                # Format 3: OpenAI format with audio_url (if supported)
                {
                    "type": "input_audio",
                    "audio_url": {
                        "url": f"data:{mime_type};base64,{audio_b64}"
                    }
                }
            ]
            
            for format_idx, audio_format in enumerate(audio_formats, 1):
                try:
                    print(f"[Audio] Trying {model} with format {format_idx}...")
                    
                    # Try with explicit instruction
                    # Voxtral is designed for audio transcription, so we need clear instructions
                    if "voxtral" in model.lower():
                        prompt_text = (
                            "Listen to the audio file and transcribe exactly what is spoken. "
                            "Return ONLY the spoken words as plain text. "
                            "Do not add any commentary, explanations, or descriptions of your capabilities. "
                            "Do not include timestamps. Just return the transcription of the spoken words."
                        )
                    else:
                        prompt_text = (
                            "You are an audio transcription expert. "
                            "Transcribe the provided audio file word-for-word. "
                            "Return ONLY the transcription text, no explanations, no apologies, no commentary. "
                            "If the audio is unclear, transcribe what you can hear."
                        )
                    
                    response = self.openai_client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an audio transcription tool. Your only job is to transcribe the spoken words from audio files. Return only the transcribed text, nothing else."
                            } if "voxtral" not in model.lower() else {
                                "role": "system",
                                "content": "You are Voxtral, an audio transcription model. Transcribe the audio file and return only the spoken words as plain text."
                            },
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": prompt_text
                                    },
                                    audio_format
                                ]
                            }
                        ],
                        max_tokens=4000,
                        temperature=0.0
                    )
                    
                    transcript = response.choices[0].message.content.strip()
                    
                    # Clean up timestamps if Voxtral includes them (format: [00:00:01.000])
                    if "voxtral" in model.lower():
                        import re
                        # Remove timestamp patterns like [00:00:01.000] or [HH:MM:SS.mmm]
                        transcript = re.sub(r'\[\d{2}:\d{2}:\d{2}\.\d{3}\]\s*', '', transcript)
                        # Remove any remaining timestamp-like patterns
                        transcript = re.sub(r'\[\d+:\d+:\d+[\.\d]*\]\s*', '', transcript)
                        transcript = transcript.strip()
                    
                    # Check if the response indicates the model can't handle audio or didn't receive it
                    # Use more specific rejection patterns to avoid false positives
                    transcript_lower = transcript.lower()
                    
                    # Specific rejection patterns (must be exact matches in context)
                    is_rejection = False
                    rejection_patterns = [
                        "i can't transcribe", "i cannot transcribe", "can't transcribe audio",
                        "i'm sorry, but i can't", "i'm sorry, i can't process",
                        "unable to transcribe", "not able to transcribe",
                        "don't support audio", "doesn't support audio",
                        "please provide the audio file", "need the audio file",
                        "i don't have access", "i don't see any audio",
                        "no audio file provided", "no audio provided"
                    ]
                    
                    # Check for rejection patterns
                    for pattern in rejection_patterns:
                        if pattern in transcript_lower:
                            is_rejection = True
                            break
                    
                    # For Voxtral, also check if it says it's a transcription service (positive indicator)
                    if "voxtral" in model.lower():
                        # Voxtral might say "I'm a professional audio transcription service" which is OK
                        if "transcription service" in transcript_lower and "can transcribe" in transcript_lower:
                            is_rejection = False  # This is actually a positive response
                    
                    if is_rejection:
                        print(f"[Audio] {model} cannot process audio (format {format_idx}): {transcript[:80]}...")
                        last_error = Exception(f"Model {model} cannot process audio: {transcript[:100]}")
                        continue
                    
                    # Check for hallucination/repetitive patterns (Voxtral sometimes generates instead of transcribing)
                    if "voxtral" in model.lower():
                        # Check for repetitive patterns that indicate hallucination
                        words = transcript.split()
                        if len(words) > 100:
                            # Check for high repetition
                            word_counts = {}
                            for word in words[:50]:  # Check first 50 words
                                word_counts[word] = word_counts.get(word, 0) + 1
                            max_repetition = max(word_counts.values()) if word_counts else 0
                            
                            # If same phrase repeats too much, it's likely hallucination
                            if max_repetition > 10 or "i can also generate" in transcript_lower:
                                print(f"[Audio] {model} appears to be hallucinating (format {format_idx}): {transcript[:80]}...")
                                last_error = Exception(f"Model {model} generated text instead of transcribing audio")
                                continue
                    
                    # If we get here and transcript is not empty and doesn't look like a rejection, it might be valid
                    # Check for reasonable transcription length (at least 20 chars for a real transcription)
                    # For Voxtral, accept longer responses even if they mention being a service
                    min_length = 50 if "voxtral" in model.lower() else 20
                    if transcript and len(transcript) > min_length:
                        print(f"[Audio] Successfully transcribed using {model} (format {format_idx})")
                        return transcript
                    elif transcript and len(transcript) > 20:
                        # Might be a valid short transcription
                        print(f"[Audio] Successfully transcribed using {model} (format {format_idx}) - short response")
                        return transcript
                    else:
                        print(f"[Audio] {model} returned invalid response (format {format_idx}): {transcript[:80]}...")
                        last_error = Exception(f"Invalid transcription from {model}: {transcript[:100]}")
                        continue
                    
                except Exception as e:
                    error_str = str(e).lower()
                    error_msg = str(e)
                    
                    # Check if it's a model capability issue
                    if any(term in error_str for term in ['audio', 'input', 'not supported', 'invalid', 'format', 'unsupported']):
                        print(f"[Audio] {model} format {format_idx} issue: {error_msg[:100]}...")
                        last_error = e
                        continue
                    elif 'rate limit' in error_str or 'quota' in error_str:
                        # Don't retry on rate limit/quota errors
                        raise e
                    else:
                        # Other error, try next format
                        print(f"[Audio] {model} format {format_idx} error: {error_msg[:100]}...")
                        last_error = e
                        continue
        
        # All models and formats failed
        error_msg = (
            f"Audio transcription failed: OpenRouter models do not support audio input via chat completions.\n"
            f"Tried models: {', '.join(fallback_models)} with multiple formats.\n"
            f"Last error: {last_error}\n\n"
            f"SOLUTION: Set OPENAI_DIRECT_API_KEY in your .env file with a direct OpenAI API key.\n"
            f"The Whisper API (direct OpenAI) is the only reliable method for audio transcription.\n"
            f"Get your OpenAI API key at: https://platform.openai.com/account/api-keys"
        )
        raise ValueError(error_msg)
    
    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type based on file extension."""
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.flac': 'audio/flac',
            '.m4a': 'audio/mp4',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.wma': 'audio/x-ms-wma',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska'
        }
        return mime_types.get(ext, 'audio/mpeg')
    
    def extract_image(self, file_path: str) -> Dict[str, Any]:
        """
        Extract visual features from image (NO OCR).
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with visual description
        """
        try:
            if not self.openai_client:
                return {
                    'visual_features': '',
                    'success': False,
                    'error': 'OpenAI API key not provided'
                }
            
            # Read and encode image
            with open(file_path, 'rb') as image_file:
                image_data = image_file.read()
            
            # Use GPT-4 Vision for visual description
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            visual_description = self._get_visual_description(base64_image)
            
            return {
                'visual_features': visual_description,
                'extraction_method': 'vision_model',
                'success': True
            }
        except Exception as e:
            error_info = handle_api_error(e)
            print(f"[Content Extractor] Image extraction error: {e} (Type: {error_info['error_type']})")
            return {
                'visual_features': '',
                'success': False,
                'error': str(e),
                'error_type': error_info['error_type']
            }
    
    def _extract_pdf_ocr(self, file_content: bytes) -> str:
        """Extract text from PDF using OCR API."""
        try:
            # Try using PyPDF2 first for text-based PDFs
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            page_count = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
            
            if text.strip():
                logger.info(f"Extracted text from PDF using PyPDF2", pages=page_count, text_length=len(text))
                return text.strip()
            
            # If no text extracted, PDF is likely image-based - convert to images and OCR
            logger.warning(f"PDF appears to be image-based (scanned). {page_count} pages detected but no text extracted.")
            if not self.openai_client:
                return f"PDF appears to be image-based (scanned document). {page_count} pages detected but no extractable text found. Text extraction requires image conversion and OCR, but OpenAI API key not available."
            
            # Try to convert PDF pages to images
            try:
                # Method 1: Try PyMuPDF (fitz) - recommended, no poppler required
                try:
                    import fitz  # PyMuPDF
                    pdf_doc = fitz.open(stream=file_content, filetype="pdf")
                    images = []
                    for page_num in range(len(pdf_doc)):
                        page = pdf_doc[page_num]
                        # Render page as image (PNG) with 2x zoom for better quality
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        img_data = pix.tobytes("png")
                        from PIL import Image
                        img = Image.open(io.BytesIO(img_data))
                        images.append(img)
                    pdf_doc.close()
                    logger.info(f"Converted PDF to {len(images)} images using PyMuPDF")
                except ImportError:
                    # Method 2: Try pdf2image (requires poppler)
                    try:
                        from pdf2image import convert_from_bytes
                        images = convert_from_bytes(file_content, dpi=200)
                        logger.info(f"Converted PDF to {len(images)} images using pdf2image")
                    except ImportError:
                        # Method 3: Fallback - return helpful error
                        return f"PDF appears to be image-based (scanned document). {page_count} pages detected but no extractable text found. To process scanned PDFs, please install PyMuPDF: pip install PyMuPDF"
                
                if not images:
                    return f"PDF appears to be image-based (scanned document). {page_count} pages detected but no extractable text found. Failed to convert PDF pages to images."
                
                # OCR each page using OpenAI Vision API
                all_text = []
                for i, img in enumerate(images):
                    try:
                        # Convert PIL Image to base64
                        buffered = io.BytesIO()
                        img.save(buffered, format="PNG")
                        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        
                        # Use OpenAI Vision API for OCR
                        response = self.openai_client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "Extract all text from this image. Return only the text content, preserving structure and formatting as much as possible. Include all visible text, numbers, and labels."
                                        },
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/png;base64,{img_base64}"
                                            }
                                        }
                                    ]
                                }
                            ],
                            max_tokens=4000
                        )
                        
                        page_text = response.choices[0].message.content.strip()
                        if page_text:
                            all_text.append(f"--- Page {i+1} ---\n{page_text}\n")
                            logger.info(f"OCR'd page {i+1}/{len(images)}", text_length=len(page_text))
                    
                    except Exception as e:
                        logger.warning(f"Failed to OCR page {i+1}", error=str(e))
                        # Continue with next page if one fails
                        continue
                
                if all_text:
                    combined_text = "\n".join(all_text)
                    logger.info("PDF OCR completed", total_pages=len(images), total_text_length=len(combined_text))
                    return combined_text
                else:
                    logger.error("PDF OCR failed on all pages", total_pages=len(images))
                    return f"PDF pages converted to images but OCR failed on all {len(images)} pages. Please check OpenAI API key and quota."
                    
            except Exception as e:
                return f"PDF appears to be image-based (scanned document). {page_count} pages detected but conversion failed: {str(e)}"
        
        except ImportError:
            return "PyPDF2 not installed. Please install it: pip install PyPDF2"
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"
    
    def _extract_docx_ocr(self, file_content: bytes) -> str:
        """Extract text from DOCX."""
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_content))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            return f"Error extracting DOCX: {str(e)}"
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _get_visual_description(self, base64_image: str) -> str:
        """Get visual description from image with retry logic - fully dynamic for any content type."""
        try:
            # Use gpt-4o for vision (better vision support than gpt-4o-mini)
            response = self.openai_client.chat.completions.create(
                model=Config.get_model_name("gpt-4o"),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Analyze this image comprehensively and provide an extremely detailed description. "
                                    "Be as SPECIFIC as possible - identify exact species, breeds, models, types, or classifications. "
                                    "For living organisms (animals, plants): identify the EXACT SPECIES if possible (e.g., 'Western Diamondback Rattlesnake' not just 'rattlesnake', "
                                    "'Golden Retriever' not just 'dog', 'Monarch Butterfly' not just 'butterfly'). "
                                    "Include distinguishing features that help with species identification (patterns, markings, colors, body structure). "
                                    "For objects: identify specific models, brands, or types (e.g., 'iPhone 14 Pro' not just 'smartphone'). "
                                    "For buildings: identify architectural style and period (e.g., 'Victorian Gothic Revival' not just 'old building'). "
                                    "For scientific content: identify specific compounds, formulas, structures by name. "
                                    "For diagrams/graphs: identify the type and what it represents. "
                                    "Include all visible details: colors, textures, composition, scene type, mood, environment, and context. "
                                    "Be thorough and maximally specific - use precise scientific/technical names when applicable."
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"  # Request high detail analysis
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000  # Increased for more detailed descriptions
            )
            
            description = response.choices[0].message.content
            
            # Check if the model refused to analyze
            refusal_patterns = [
                "i'm unable to analyze",
                "i cannot analyze",
                "i can't analyze",
                "unable to provide",
                "cannot provide a description",
                "if you describe what you're seeing"
            ]
            
            description_lower = description.lower()
            if any(pattern in description_lower for pattern in refusal_patterns):
                raise ValueError(f"Vision model refused to analyze image: {description[:100]}")
            
            return description
            
        except Exception as e:
            print(f"[Content Extractor] Vision analysis error: {e}")
            raise

