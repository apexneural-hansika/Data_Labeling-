"""
Quality Check Agent - Validates the labeling quality
"""
from typing import Dict, Any, Optional
from openai import OpenAI


class QualityCheckAgent:
    """Validates the quality of labeling results."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the quality check agent.
        
        Args:
            openai_api_key: API key for OpenAI (optional, for advanced checks)
        """
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
    
    def check_quality(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform quality checks on the labeling result.
        
        Args:
            result: The labeling result dictionary
            
        Returns:
            Dictionary with quality metrics and validation results
        """
        quality_issues = []
        quality_score = 1.0
        
        # Normalize category - check multiple locations
        category = result.get('category') or result.get('labels', {}).get('category') or 'uncategorized'
        if 'category' not in result:
            result['category'] = category  # Normalize to top level
        
        # Check if required fields are present
        required_fields = ['file_name', 'modality']
        for field in required_fields:
            if field not in result or not result[field]:
                quality_issues.append(f"Missing required field: {field}")
                quality_score -= 0.2
        
        # Category check (now that we've normalized it)
        if not category or category in ['uncategorized', 'unknown']:
            quality_issues.append("Category is missing or uncategorized")
            quality_score -= 0.2
        
        # Modality-specific checks
        modality = result.get('modality', '')
        
        if modality == 'text_document' or modality == 'audio':
            if not result.get('raw_text') or len(result.get('raw_text', '').strip()) < 10:
                quality_issues.append("Raw text is too short or missing")
                quality_score -= 0.3
        elif modality == 'image':
            if not result.get('visual_features') or len(result.get('visual_features', '').strip()) < 10:
                quality_issues.append("Visual features are missing or too short")
                quality_score -= 0.3
        
        # Check labels
        labels = result.get('labels', {})
        if not labels or len(labels) == 0:
            quality_issues.append("No labels generated")
            quality_score -= 0.2
        else:
            # Validate label quality
            if isinstance(labels, dict):
                # Modality-specific meaningful fields
                if modality == 'image':
                    # For images, check for image-specific fields (including nested structures)
                    image_fields = ['image', 'objects', 'colors', 'scene_type', 'subject', 'style', 'features', 'design', 'construction', 'visual_effects']
                    has_meaningful_labels = any(
                        field in labels and labels[field] and 
                        (isinstance(labels[field], dict) and len(labels[field]) > 0 or 
                         isinstance(labels[field], list) and len(labels[field]) > 0 or
                         isinstance(labels[field], str) and len(str(labels[field])) > 0)
                        for field in image_fields
                    )
                    # Also check if there's a nested 'image' object with substantial content
                    if not has_meaningful_labels and 'image' in labels:
                        image_obj = labels['image']
                        if isinstance(image_obj, dict):
                            # Check if nested image object has meaningful content
                            nested_fields = ['subject', 'style', 'features', 'design', 'construction', 'color', 'visual_effects']
                            has_meaningful_labels = any(
                                field in image_obj and image_obj[field] and
                                (isinstance(image_obj[field], dict) and len(image_obj[field]) > 0 or
                                 isinstance(image_obj[field], list) and len(image_obj[field]) > 0 or
                                 isinstance(image_obj[field], str) and len(str(image_obj[field])) > 0)
                                for field in nested_fields
                            )
                            # If nested dict has multiple keys, it's likely meaningful
                            if not has_meaningful_labels and len(image_obj) >= 3:
                                has_meaningful_labels = True
                elif modality in ['text_document', 'audio']:
                    # For text/audio, check for text-specific fields
                    text_fields = ['topics', 'entities', 'keywords', 'sentiment']
                    has_meaningful_labels = any(field in labels and labels[field] for field in text_fields)
                else:
                    # Generic check
                    meaningful_fields = ['topics', 'entities', 'keywords', 'sentiment', 'objects', 'colors', 'scene_type', 'image', 'subject']
                    has_meaningful_labels = any(field in labels and labels[field] for field in meaningful_fields)
                
                if not has_meaningful_labels:
                    quality_issues.append("Labels lack meaningful content")
                    quality_score -= 0.15
                
                # Check for error fields in labels
                if 'error' in labels or 'error_type' in labels:
                    quality_issues.append("Labels contain error information")
                    quality_score -= 0.1
                
                # Validate list fields are actually lists
                list_fields = ['topics', 'entities', 'keywords', 'objects', 'colors']
                for field in list_fields:
                    if field in labels and not isinstance(labels[field], list):
                        quality_issues.append(f"Label field '{field}' is not a list")
                        quality_score -= 0.05
        
        # Check confidence (check multiple field names and use the highest)
        confidence = max(
            result.get('confidence', 0.0),
            result.get('label_confidence', 0.0),
            result.get('category_confidence', 0.0)
        )
        
        # If we found confidence in a different field, normalize it
        if 'confidence' not in result and confidence > 0:
            result['confidence'] = confidence
        
        if confidence < 0.5:
            quality_issues.append(f"Low confidence score: {confidence}")
            quality_score -= 0.1
        
        # Check for processing notes that indicate issues
        if 'processing_note' in labels and 'chunks' in str(labels.get('processing_note', '')):
            # Chunked processing is okay, but note it
            pass  # Not an issue, just informational
        
        # Check category quality
        category = result.get('category', '')
        if category and category not in ['uncategorized', 'unknown']:
            # Check if category was normalized (good sign)
            if 'original_category' in result:
                pass  # Category was normalized, which is good
        
        # Ensure quality score is between 0 and 1
        quality_score = max(0.0, min(1.0, quality_score))
        
        # Determine quality status
        if quality_score >= 0.8:
            status = 'high'
        elif quality_score >= 0.6:
            status = 'medium'
        else:
            status = 'low'
        
        return {
            'quality_score': round(quality_score, 2),
            'quality_status': status,
            'issues': quality_issues,
            'passed': len(quality_issues) == 0,
            'recommendations': self._generate_recommendations(quality_issues, result)
        }
    
    def _generate_recommendations(self, issues: list, result: Dict[str, Any]) -> list:
        """Generate recommendations based on quality issues."""
        recommendations = []
        
        if 'Raw text is too short' in str(issues):
            recommendations.append("Consider re-extracting content with different OCR settings")
        
        if 'Visual features are missing' in str(issues):
            recommendations.append("Try re-processing the image with a different vision model")
        
        if 'Category is missing' in str(issues):
            recommendations.append("Content may be too ambiguous - consider manual categorization")
        
        if 'No labels generated' in str(issues):
            recommendations.append("Content may be too sparse - consider enriching the input")
        
        if 'Labels lack meaningful content' in str(issues):
            recommendations.append("Try reprocessing with different content or check if content extraction was successful")
        
        if 'Low confidence' in str(issues):
            recommendations.append("Consider manual review or reprocessing with different settings")
        
        if 'error' in str(issues).lower():
            recommendations.append("Check API connectivity and quota limits")
        
        if not recommendations:
            recommendations.append("Quality check passed - result looks good!")
        
        return recommendations

