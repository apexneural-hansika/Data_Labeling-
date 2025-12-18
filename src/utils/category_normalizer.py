"""
Category normalization for consistency
"""
from typing import Dict, Optional


# Category normalization mapping
CATEGORY_MAPPING = {
    # Business/Finance
    'business_report': 'business_report',
    'business_document': 'business_report',
    'financial_report': 'business_report',
    'financial_document': 'business_report',
    'annual_report': 'business_report',
    'quarterly_report': 'business_report',
    'earnings_report': 'business_report',
    
    # Academic/Scientific
    'scientific_paper': 'scientific_paper',
    'research_paper': 'scientific_paper',
    'academic_paper': 'scientific_paper',
    'research_article': 'scientific_paper',
    'scientific_article': 'scientific_paper',
    'journal_article': 'scientific_paper',
    
    # News/Media
    'news_article': 'news_article',
    'news': 'news_article',
    'article': 'news_article',
    'blog_post': 'news_article',
    'press_release': 'news_article',
    
    # Technical
    'technical_documentation': 'technical_documentation',
    'technical_doc': 'technical_documentation',
    'documentation': 'technical_documentation',
    'user_manual': 'technical_documentation',
    'api_documentation': 'technical_documentation',
    
    # Transcripts
    'transcript_conversation': 'transcript',
    'transcript': 'transcript',
    'meeting_transcript': 'transcript',
    'interview_transcript': 'transcript',
    'audio_transcript': 'transcript',
    
    # Images
    'nature_landscape': 'nature_landscape',
    'landscape': 'nature_landscape',
    'portrait_photography': 'portrait',
    'portrait': 'portrait',
    'product_image': 'product_image',
    'product': 'product_image',
    'medical_scan': 'medical_image',
    'medical_image': 'medical_image',
    'architectural_design': 'architectural',
    'architecture': 'architectural',
    
    # Other
    'uncategorized': 'uncategorized',
    'unknown': 'uncategorized',
}


def normalize_category(category: Optional[str]) -> str:
    """
    Normalize category name for consistency.
    
    Args:
        category: Category name to normalize
        
    Returns:
        Normalized category name
    """
    if not category:
        return 'uncategorized'
    
    category_lower = category.lower().strip().replace(' ', '_')
    
    # Direct mapping
    if category_lower in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[category_lower]
    
    # Partial matching for similar categories
    for key, value in CATEGORY_MAPPING.items():
        if key in category_lower or category_lower in key:
            return value
    
    # If no match, return cleaned version
    return category_lower







