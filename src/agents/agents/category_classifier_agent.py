"""
Category Classifier Agent - Assigns dynamic categories based on content
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from openai import OpenAI

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config import Config
from utils.api_utils import retry_with_backoff, handle_api_error
from utils.category_normalizer import normalize_category


class CategoryClassifierAgent:
    """Classifies content into dynamic categories based on extracted content."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the category classifier.
        
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
    
    def classify_category(self, modality: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify content into a dynamic category.
        
        Args:
            modality: File modality (text_document, image, audio)
            content: Extracted content dictionary
            
        Returns:
            Dictionary with category classification
        """
        try:
            if not self.openai_client:
                return {
                    'category': 'uncategorized',
                    'confidence': 0.0,
                    'reasoning': 'API key not provided'
                }
            
            # Prepare content for classification
            if modality == 'text_document' or modality == 'audio':
                text_content = content.get('raw_text', '')
                
                # Validate we have text content
                if not text_content or not text_content.strip():
                    print(f"[Category Classifier] ERROR: No raw_text found for {modality}")
                    print(f"[Category Classifier] Available keys in content: {list(content.keys())}")
                    return {
                        'category': 'uncategorized',
                        'confidence': 0.0,
                        'reasoning': f'No text content extracted from {modality}'
                    }
                
                # Use larger sample for better classification (increased from 2000 to 5000)
                # For very large documents, sample from beginning, middle, and end
                if len(text_content) > 5000:
                    # Sample from different parts of the document
                    sample_size = 2000
                    samples = [
                        text_content[:sample_size],  # Beginning
                        text_content[len(text_content)//2 - sample_size//2:len(text_content)//2 + sample_size//2],  # Middle
                        text_content[-sample_size:]  # End
                    ]
                    text_content = "\n\n[...]\n\n".join(samples)
                else:
                    text_content = text_content[:5000]
                
                prompt = f"Analyze the following content and assign it to a single, specific, descriptive category. The category should naturally emerge from the content itself - be creative and precise. Return ONLY the category name, nothing else.\n\nContent:\n{text_content}"
            
            elif modality == 'image':
                visual_content = content.get('visual_features', '')
                
                # Validate we have visual content
                if not visual_content or not visual_content.strip():
                    print(f"[Category Classifier] ERROR: No visual_features found for image")
                    print(f"[Category Classifier] Available keys in content: {list(content.keys())}")
                    return {
                        'category': 'uncategorized',
                        'confidence': 0.0,
                        'reasoning': 'No visual features extracted from image'
                    }
                
                print(f"[Category Classifier] Classifying image with visual_features length: {len(visual_content)}")
                prompt = f"Based on this visual description, assign the image to a single, specific, descriptive category. The category should naturally emerge from what's in the image - be creative and precise. Return ONLY the category name, nothing else.\n\nVisual Description:\n{visual_content}"
            
            else:
                return {
                    'category': 'uncategorized',
                    'confidence': 0.0,
                    'reasoning': f'Unknown modality: {modality}'
                }
            
            # Get category from LLM with retry logic
            category = self._classify_with_retry(prompt)
            
            # Normalize category for consistency
            normalized_category = normalize_category(category)
            
            return {
                'category': normalized_category,
                'original_category': category,  # Keep original for reference
                'confidence': 0.85,  # Confidence score
                'reasoning': f'Classified as {normalized_category} based on content analysis'
            }
        except Exception as e:
            error_info = handle_api_error(e)
            print(f"[Category Classifier] Error: {e} (Type: {error_info['error_type']})")
            return {
                'category': 'uncategorized',
                'confidence': 0.0,
                'error': str(e),
                'error_type': error_info['error_type']
            }
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _classify_with_retry(self, prompt: str) -> str:
        """Classify category with retry logic."""
        response = self.openai_client.chat.completions.create(
            model=Config.get_model_name("gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a content categorization expert. Return only the category name."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.3
        )
        
        category = response.choices[0].message.content.strip().lower().replace(' ', '_')
        return category

