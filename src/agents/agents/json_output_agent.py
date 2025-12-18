"""
Final JSON Output Agent - Formats the final output
"""
from typing import Dict, Any
import json
from datetime import datetime


class JSONOutputAgent:
    """Formats the final labeling result as JSON."""
    
    def format_output(self, result: Dict[str, Any], quality_check: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the final output with all required fields.
        
        Args:
            result: The labeling result dictionary
            quality_check: Quality check results
            
        Returns:
            Formatted JSON dictionary
        """
        # Ensure labels is always a dictionary
        labels = result.get('labels', {})
        if not labels or not isinstance(labels, dict):
            labels = {
                'category': result.get('category', 'unknown'),
                'modality': result.get('modality', 'unknown'),
                'note': 'Labels not available'
            }
        
        # Build the final output structure
        output = {
            'file_name': result.get('file_name', ''),
            'modality': result.get('modality', ''),
            'raw_text': result.get('raw_text', '') if result.get('modality') in ['text_document', 'audio'] else None,
            'visual_features': result.get('visual_features', '') if result.get('modality') == 'image' else None,
            'category': result.get('category', ''),
            'labels': labels,
            'confidence': result.get('confidence', 0.0),
            'quality_check': {
                'quality_score': quality_check.get('quality_score', 0.0),
                'quality_status': quality_check.get('quality_status', 'unknown'),
                'passed': quality_check.get('passed', False)
            },
            'timestamp': datetime.now().isoformat(),
            'processing_metadata': {
                'extraction_method': result.get('extraction_method', ''),
                'category_reasoning': result.get('category_reasoning', ''),
                'label_confidence': result.get('label_confidence', 0.0)
            }
        }
        
        return output
    
    def save_json(self, output: Dict[str, Any], output_path: str) -> bool:
        """
        Save the output to a JSON file.
        
        Args:
            output: The output dictionary
            output_path: Path to save the JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving JSON: {e}")
            return False

