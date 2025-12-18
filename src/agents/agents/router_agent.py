"""
Router Agent - Classifies file modality (text_document, image, audio)
"""
import os
from typing import Dict, Any


class RouterAgent:
    """Classifies the modality of uploaded files."""
    
    # Text document extensions
    TEXT_DOCUMENT_EXTENSIONS = {'.pdf', '.txt', '.docx', '.doc', '.csv', '.xlsx', '.xls'}
    
    # Image extensions
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'}
    
    # Audio extensions
    AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma', '.mp4', '.avi', '.mov', '.mkv'}
    
    def classify_modality(self, file_path: str) -> Dict[str, Any]:
        """
        Classify the modality of a file based on its extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with modality classification and metadata
        """
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        
        if file_ext in self.TEXT_DOCUMENT_EXTENSIONS:
            modality = 'text_document'
        elif file_ext in self.IMAGE_EXTENSIONS:
            modality = 'image'
        elif file_ext in self.AUDIO_EXTENSIONS:
            modality = 'audio'
        else:
            modality = 'unknown'
        
        return {
            'file_name': file_name,
            'file_path': file_path,
            'modality': modality,
            'extension': file_ext,
            'confidence': 1.0 if modality != 'unknown' else 0.0
        }

