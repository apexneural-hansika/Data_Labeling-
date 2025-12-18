# AgenticAI

An intelligent, multi-modal data labeling platform powered by agentic AI. AgenticAI automatically labels text documents, images, audio files, and any content type using a pipeline of specialized AI agents with dynamic, adaptive intelligence.

## Features

- **Multi-Modal Support**: Process text documents, images, and audio files
- **Intelligent OCR**: OCR applied only to text documents (PDF, TXT, DOCX, CSV), NOT images
- **Visual Image Analysis**: Images are analyzed visually (objects, scenes, composition) without OCR
- **Audio Transcription**: Audio files are transcribed using Whisper before labeling
- **Dynamic Categories**: Categories are automatically inferred from content
- **Quality Assurance**: Built-in quality checking for all labeled outputs
- **Beautiful Web Interface**: Premium, classy design with glassmorphism effects
- **Dynamic Intelligence**: Adapts to any content type - animals, buildings, chemical compounds, knowledge graphs, and more
- **Intelligent Feature Extraction**: Automatically identifies breeds, architectural styles, compound names, graph structures, and domain-specific attributes

## System Architecture

The system consists of 6 specialized agents:

1. **Router Agent** - Classifies file modality (text_document, image, audio)
2. **Content Extractor Agent** - Extracts content based on modality
   - Text documents: OCR using DeepSeek/OpenAI
   - Audio: Whisper transcription
   - Images: Visual description (NO OCR)
3. **Category Classifier Agent** - Assigns dynamic categories
4. **Label Generator Agent** - Extracts structured labels
5. **Quality Check Agent** - Validates labeling quality
6. **JSON Output Agent** - Formats final output

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (required)
- DeepSeek API key (optional, for OCR)

### Setup

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up API keys using one of these methods:

**Method 1: .env File (Recommended)**
Create a `.env` file in the project root:
```bash
# Copy the example file
cp .env.example .env

# Then edit .env and add your keys:
OPENAI_API_KEY=your-openai-api-key-here
# If using OpenRouter, also set a direct OpenAI key for Whisper:
OPENAI_DIRECT_API_KEY=your-direct-openai-api-key-here  # Required if OPENAI_API_KEY is an OpenRouter key
DEEPSEEK_API_KEY=your-deepseek-api-key-here  # Optional
```

**Method 2: Environment Variables**
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-openai-api-key"
$env:OPENAI_DIRECT_API_KEY="your-direct-openai-api-key"  # Required if using OpenRouter
$env:DEEPSEEK_API_KEY="your-deepseek-api-key"  # Optional

# Linux/Mac
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_DIRECT_API_KEY="your-direct-openai-api-key"  # Required if using OpenRouter
export DEEPSEEK_API_KEY="your-deepseek-api-key"  # Optional
```

**Method 3: Edit config.py**
Open `config.py` and set your API keys directly:
```python
OPENAI_API_KEY = "your-openai-api-key-here"
DEEPSEEK_API_KEY = "your-deepseek-api-key-here"  # Optional
```

**Note:** The UI no longer requires API key input - keys are configured via .env file, environment variables, or config.py.

## Usage

### Running the Web Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Upload a file:
   - Select a file (text, image, or audio)
   - Click "Process File"
   - API keys are automatically loaded from environment variables or config.py

4. View results:
   - The system will process your file through all 6 agents
   - Results will be displayed with quality scores
   - JSON output can be copied to clipboard

### Supported File Types

**Text Documents:**
- PDF (.pdf)
- Text (.txt)
- Word (.docx, .doc)
- CSV (.csv)
- Excel (.xlsx, .xls)

**Images:**
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- WebP (.webp)
- TIFF (.tiff)
- SVG (.svg)

**Audio:**
- MP3 (.mp3)
- WAV (.wav)
- FLAC (.flac)
- M4A (.m4a)
- AAC (.aac)
- OGG (.ogg)
- WMA (.wma)
- Video files with audio (.mp4, .avi, .mov, .mkv)

### Output Format

The system generates JSON output with the following structure:

```json
{
  "file_name": "example.pdf",
  "modality": "text_document",
  "raw_text": "Extracted text content...",
  "visual_features": null,
  "category": "business_report",
  "labels": {
    "topics": ["finance", "analysis"],
    "entities": ["Company ABC"],
    "keywords": ["revenue", "growth"],
    "sentiment": "neutral",
    "language": "en"
  },
  "confidence": 0.85,
  "quality_check": {
    "quality_score": 0.9,
    "quality_status": "high",
    "passed": true
  },
  "timestamp": "2024-01-15T10:30:00",
  "processing_metadata": {
    "extraction_method": "ocr",
    "category_reasoning": "Classified as business_report based on content analysis"
  }
}
```

## Project Structure

```
data_labeling/
├── agents/
│   ├── __init__.py
│   ├── router_agent.py          # Modality classification
│   ├── content_extractor_agent.py  # Content extraction
│   ├── category_classifier_agent.py  # Category assignment
│   ├── label_generator_agent.py  # Label generation
│   ├── quality_check_agent.py    # Quality validation
│   └── json_output_agent.py      # JSON formatting
├── frontend/
│   ├── index.html               # Frontend HTML (served via Flask)
│   ├── style.css                # Styling
│   └── script.js                # Frontend JavaScript
├── static/                      # Flask static files
├── templates/                   # Flask templates
├── uploads/                     # Temporary upload storage
├── output/                      # Generated JSON outputs
├── app.py                       # Flask web application
├── orchestrator.py              # Main orchestration logic
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Important Notes

- **OCR on Text Documents Only**: OCR is applied to PDF, DOCX, and other text documents. Images are analyzed visually without OCR.
- **API Keys**: 
  - OpenAI API key is required for all operations
  - **Audio Transcription**: 
    - **Best Option**: Set `OPENAI_DIRECT_API_KEY` with a direct OpenAI key for Whisper API (best quality, fastest)
    - **Fallback**: If using OpenRouter only, the system will automatically use audio-capable models (`openai/gpt-4o`, `openai/gpt-4o-mini`) via chat completions
  - Set `OPENAI_DIRECT_API_KEY` with your OpenAI key if `OPENAI_API_KEY` is an OpenRouter key
  - DeepSeek API key is optional but recommended for better OCR results
- **File Size Limit**: Maximum file size is 100MB (25MB for audio files due to Whisper API limit)
- **Processing Time**: Processing time depends on file size and API response times

## Troubleshooting

### Common Issues

1. **"OpenAI API key not configured"**
   - Make sure you've created a `.env` file with `OPENAI_API_KEY=your-key` or set it as an environment variable
   - Check that the `.env` file is in the project root directory
   - Verify the key is set correctly: check `.env` file or `echo $OPENAI_API_KEY` (Linux/Mac) or `$env:OPENAI_API_KEY` (PowerShell)

2. **"Content extraction failed"**
   - Check that your API keys are valid
   - Ensure the file format is supported
   - For large files, processing may take longer

3. **"Unknown file type"**
   - The file extension is not in the supported list
   - Check the supported file types section

4. **"Error code: 401 - Incorrect API key provided" for audio files**
   - This occurs when using an OpenRouter key (`sk-or-...`) for Whisper transcription
   - Whisper API requires a direct OpenAI API key (starts with `sk-`, not `sk-or-`)
   - **Solution Options**:
     - **Option 1 (Recommended)**: Set `OPENAI_DIRECT_API_KEY` in your `.env` file with a valid OpenAI API key for direct Whisper API access (best quality, fastest)
     - **Option 2 (Fallback)**: The system will automatically try to use OpenRouter models that support audio (e.g., `openai/gpt-4o`) via chat completions with base64-encoded audio
   - Get your OpenAI API key at: https://platform.openai.com/account/api-keys
   - Example `.env` file:
     ```
     OPENAI_API_KEY=sk-or-v1-...  # Your OpenRouter key
     OPENAI_DIRECT_API_KEY=sk-...  # Your OpenAI key for Whisper (optional but recommended)
     USE_OPENROUTER=true
     ```
   - **Note**: If `OPENAI_DIRECT_API_KEY` is not set, the system will automatically fallback to OpenRouter audio-capable models (`openai/gpt-4o`, `openai/gpt-4o-mini`) for transcription

## License

This project is provided as-is for educational and development purposes.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

