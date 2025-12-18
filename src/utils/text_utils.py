"""
Text processing utilities for chunking and merging
"""
from typing import List, Dict, Any, Set


def split_text_with_overlap(text: str, chunk_size: int = 10000, overlap: int = 500) -> List[str]:
    """
    Split text into chunks with overlap to preserve context.
    
    Args:
        text: Text to split
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # If this isn't the last chunk, try to break at a sentence boundary
        if end < len(text):
            # Look for sentence endings within the last 200 chars
            search_start = max(start + chunk_size - 200, start)
            for i in range(end - 1, search_start, -1):
                if text[i] in '.!?\n':
                    end = i + 1
                    break
        
        chunk = text[start:end]
        chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks


def merge_labels(label_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge labels from multiple chunks into a single label dictionary.
    
    Args:
        label_results: List of label dictionaries from different chunks
        
    Returns:
        Merged label dictionary
    """
    if not label_results:
        return {}
    
    merged = {
        'topics': set(),
        'entities': set(),
        'keywords': set(),
        'sentiments': [],
        'languages': set(),
        'content_types': set(),
        'objects': set(),
        'colors': set(),
        'scene_types': set(),
        'other_fields': {}
    }
    
    for labels in label_results:
        if not isinstance(labels, dict):
            continue
            
        # Merge topics
        if 'topics' in labels:
            topics = labels['topics']
            if isinstance(topics, list):
                merged['topics'].update(topics)
        
        # Merge entities
        if 'entities' in labels:
            entities = labels['entities']
            if isinstance(entities, list):
                merged['entities'].update(entities)
        
        # Merge keywords
        if 'keywords' in labels:
            keywords = labels['keywords']
            if isinstance(keywords, list):
                merged['keywords'].update(keywords)
        
        # Collect sentiments for averaging
        if 'sentiment' in labels:
            sentiment = labels['sentiment']
            if sentiment and isinstance(sentiment, str):
                merged['sentiments'].append(sentiment.lower())
        
        # Collect languages
        if 'language' in labels:
            lang = labels['language']
            if lang:
                merged['languages'].add(str(lang).lower())
        
        # Collect content types
        if 'content_type' in labels:
            ct = labels['content_type']
            if ct:
                merged['content_types'].add(str(ct))
        
        # Image-specific fields
        if 'objects' in labels:
            objects = labels['objects']
            if isinstance(objects, list):
                merged['objects'].update(objects)
        
        if 'colors' in labels:
            colors = labels['colors']
            if isinstance(colors, list):
                merged['colors'].update(colors)
        
        if 'scene_type' in labels:
            scene = labels['scene_type']
            if scene:
                merged['scene_types'].add(str(scene))
        
        # Store other fields (take first non-empty value)
        for key, value in labels.items():
            if key not in ['topics', 'entities', 'keywords', 'sentiment', 'language', 
                          'content_type', 'objects', 'colors', 'scene_type', 
                          'category', 'modality', 'note', 'error']:
                if key not in merged['other_fields'] or not merged['other_fields'][key]:
                    merged['other_fields'][key] = value
    
    # Build final merged dictionary
    final_labels = {}
    
    # Convert sets to lists and sort
    if merged['topics']:
        final_labels['topics'] = sorted(list(merged['topics']))
    if merged['entities']:
        final_labels['entities'] = sorted(list(merged['entities']))
    if merged['keywords']:
        final_labels['keywords'] = sorted(list(merged['keywords']))
    
    # Determine dominant sentiment
    if merged['sentiments']:
        sentiment_counts = {}
        for s in merged['sentiments']:
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
        final_labels['sentiment'] = max(sentiment_counts, key=sentiment_counts.get)
    
    # Use most common language
    if merged['languages']:
        final_labels['language'] = list(merged['languages'])[0]  # Take first, could improve with voting
    
    # Use most common content type
    if merged['content_types']:
        final_labels['content_type'] = list(merged['content_types'])[0]
    
    # Image-specific
    if merged['objects']:
        final_labels['objects'] = sorted(list(merged['objects']))
    if merged['colors']:
        final_labels['colors'] = sorted(list(merged['colors']))
    if merged['scene_types']:
        final_labels['scene_type'] = list(merged['scene_types'])[0]  # Take first
    
    # Add other fields
    final_labels.update(merged['other_fields'])
    
    return final_labels







