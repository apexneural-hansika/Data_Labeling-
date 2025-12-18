"""
Label Generator Agent - Extracts structured labels from content
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from openai import OpenAI
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config import Config
from utils.api_utils import retry_with_backoff, handle_api_error


class LabelGeneratorAgent:
    """Generates structured labels from extracted content."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the label generator.
        
        Args:
            openai_api_key: API key for OpenAI/OpenRouter
        """
        if openai_api_key:
            base_url = Config.get_base_url()
            self.openai_client = OpenAI(
                api_key=openai_api_key,
                base_url=base_url
            ) if base_url else OpenAI(api_key=openai_api_key)
        else:
            self.openai_client = None
    
    def generate_labels(self, modality: str, content: Dict[str, Any], category: str) -> Dict[str, Any]:
        """
        Generate structured labels from content.
        
        Args:
            modality: File modality
            content: Extracted content dictionary
            category: Assigned category
            
        Returns:
            Dictionary with structured labels
        """
        try:
            if not self.openai_client:
                # Return basic labels even without API
                return {
                    'labels': {
                        'category': category,
                        'modality': modality,
                        'note': 'Labels generated without API - basic information only'
                    },
                    'confidence': 0.3
                }
            
            # Prepare content for label extraction
            if modality == 'text_document' or modality == 'audio':
                text_content = content.get('raw_text', '')
                
                # Check if content is empty or too short
                if not text_content or len(text_content.strip()) < 10:
                    return {
                        'labels': {
                            'category': category,
                            'modality': modality,
                            'content_length': len(text_content) if text_content else 0,
                            'note': 'Content too short or empty for detailed labeling',
                            'extraction_status': 'minimal'
                        },
                        'confidence': 0.4
                    }
                
                # Process document directly without chunking
                return self._generate_labels_for_chunk(text_content, category, modality)
                    
            elif modality == 'image':
                visual_content = content.get('visual_features', '')
                
                if not visual_content or len(visual_content.strip()) < 10:
                    return {
                        'labels': {
                            'category': category,
                            'modality': modality,
                            'note': 'Visual features not available for detailed labeling',
                            'extraction_status': 'minimal'
                        },
                        'confidence': 0.4
                    }
                
                return self._generate_labels_for_image(visual_content, category, modality)
            else:
                return {
                    'labels': {
                        'category': category,
                        'modality': modality,
                        'note': 'Unknown modality - basic information only'
                    },
                    'confidence': 0.3
                }
        except Exception as e:
            error_info = handle_api_error(e)
            print(f"[Label Generator] Error: {e} (Type: {error_info['error_type']})")
            return {
                'labels': {
                    'category': category,
                    'modality': modality,
                    'error': str(e),
                    'error_type': error_info['error_type'],
                    'note': 'Label extraction failed - using fallback labels'
                },
                'confidence': 0.2
            }
    
    def _generate_labels_for_chunk(self, text_content: str, category: str, modality: str) -> Dict[str, Any]:
        """Generate labels for a single text chunk - fully dynamic, zero hardcoding."""
        prompt = f"""You are an intelligent content analysis expert. Analyze the following content and extract ALL relevant information as a comprehensive JSON object.

DO NOT use any predefined templates or structures. Instead:
1. Examine the actual content carefully
2. Identify what information is present and meaningful
3. Create a JSON structure that naturally fits THIS specific content
4. Include whatever fields make sense for THIS content

Guidelines:
- Be comprehensive - extract all meaningful information
- Be specific - use precise terms and classifications
- Be adaptive - structure should match the content type naturally
- Be flat - avoid unnecessary nesting
- Include both general attributes AND domain-specific details

Content Category: {category}
Modality: {modality}

Content:
{text_content[:15000]}

Return ONLY valid JSON with whatever fields are relevant for this specific content. The structure should emerge from the content itself, not from a template."""
        
        return self._call_llm_for_labels(prompt, category, modality)
    
    def _generate_labels_for_image(self, visual_content: str, category: str, modality: str) -> Dict[str, Any]:
        """Generate labels for image - fully dynamic, zero hardcoding."""
        prompt = f"""You are an intelligent visual content analysis expert. Analyze the following image description and extract ALL relevant information as a comprehensive JSON object.

DO NOT use any predefined templates or structures. Instead:
1. Examine the visual description carefully
2. Identify what elements, objects, and characteristics are present
3. Create a JSON structure that naturally represents THIS specific image
4. Include whatever fields make sense for THIS image

Guidelines:
- Be comprehensive - extract all visible and identifiable information
- Be specific - use precise names, types, and classifications
- Be adaptive - structure should match what's actually in the image
- Be flat - avoid unnecessary nesting
- Include both general visual attributes AND domain-specific details

Content Category: {category}

Visual Description:
{visual_content}

Return ONLY valid JSON with whatever fields are relevant for this specific image. The structure should emerge from what you see in the description, not from a template."""
        
        return self._call_llm_for_labels(prompt, category, modality)
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _call_llm_for_labels(self, prompt: str, category: str, modality: str) -> Dict[str, Any]:
        """Call LLM for label extraction with retry logic."""
        try:
            # Get labels from LLM with retry logic
            response = self.openai_client.chat.completions.create(
                model=Config.get_model_name("gpt-4o-mini"),
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "You are an intelligent content analysis expert. Your job is to analyze content "
                            "and extract ALL relevant information as structured JSON. "
                            "DO NOT use predefined templates. Instead, examine each piece of content individually "
                            "and create a JSON structure that naturally fits that specific content. "
                            "Be comprehensive, specific, and adaptive. The structure should emerge from the content itself. "
                            "Always return valid JSON format. Never return empty objects."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=2000,
                temperature=0.3
            )
            
            labels_json = response.choices[0].message.content
            
            # Try to parse JSON with better error handling
            try:
                labels = json.loads(labels_json)
            except json.JSONDecodeError as e:
                # Try to extract JSON from response if it's wrapped in text
                import re
                json_match = re.search(r'\{.*\}', labels_json, re.DOTALL)
                if json_match:
                    labels = json.loads(json_match.group())
                else:
                    raise e
            
            # Validate that we got meaningful labels
            if not labels or len(labels) == 0:
                labels = {
                    'category': category,
                    'modality': modality,
                    'note': 'Label extraction returned empty results'
                }
            
            # Ensure we have at least basic fields
            if 'category' not in labels:
                labels['category'] = category
            if 'modality' not in labels:
                labels['modality'] = modality
            
            return {
                'labels': labels,
                'confidence': 0.80
            }
        except json.JSONDecodeError as e:
            print(f"[Label Generator] JSON decode error: {e}")
            print(f"[Label Generator] Response was: {labels_json[:200] if 'labels_json' in locals() else 'N/A'}")
            return {
                'labels': {
                    'category': category,
                    'modality': modality,
                    'error': 'Failed to parse label JSON',
                    'note': 'Label extraction encountered a parsing error'
                },
                'confidence': 0.2
            }

