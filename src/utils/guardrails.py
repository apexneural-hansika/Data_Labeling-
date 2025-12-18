"""
Guardrails system for content safety, validation, and output filtering
"""
import re
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logger import get_system_logger
from config import Config

logger = get_system_logger()


class Guardrails:
    """Content safety guardrails and validation."""
    
    def __init__(
        self,
        enable_content_filter: Optional[bool] = None,
        enable_pii_detection: Optional[bool] = None,
        enable_category_restrictions: Optional[bool] = None,
        allowed_categories: Optional[List[str]] = None,
        blocked_categories: Optional[List[str]] = None,
        min_quality_threshold: Optional[float] = None
    ):
        """
        Initialize guardrails.
        
        Args:
            enable_content_filter: Enable content safety filtering
            enable_pii_detection: Enable PII detection
            enable_category_restrictions: Enable category allow/block lists
            allowed_categories: List of allowed categories (None = all allowed)
            blocked_categories: List of blocked categories
            min_quality_threshold: Minimum quality score to pass
        """
        # Use config defaults if not provided
        self.enable_content_filter = enable_content_filter if enable_content_filter is not None else Config.ENABLE_CONTENT_FILTER
        self.enable_pii_detection = enable_pii_detection if enable_pii_detection is not None else Config.ENABLE_PII_DETECTION
        self.enable_category_restrictions = enable_category_restrictions if enable_category_restrictions is not None else Config.ENABLE_CATEGORY_RESTRICTIONS
        self.allowed_categories = allowed_categories if allowed_categories is not None else Config.ALLOWED_CATEGORIES
        self.blocked_categories = blocked_categories if blocked_categories is not None else Config.BLOCKED_CATEGORIES
        self.min_quality_threshold = min_quality_threshold if min_quality_threshold is not None else Config.MIN_QUALITY_THRESHOLD
        
        # Harmful content patterns (can be customized)
        self.harmful_patterns = [
            r'\b(violence|violent|harm|kill|murder|attack|assault)\b',
            r'\b(hate|racist|discrimination|bigotry)\b',
            r'\b(illegal|drug|weapon|explosive)\b',
            r'\b(self.harm|suicide|self.injury)\b',
            # Add more patterns as needed
        ]
        
        # PII patterns
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'passport': r'\b[A-Z]{1,2}\d{6,9}\b',
        }
        
        logger.info("Guardrails initialized",
                   content_filter=self.enable_content_filter,
                   pii_detection=self.enable_pii_detection,
                   category_restrictions=self.enable_category_restrictions,
                   min_quality=self.min_quality_threshold)
    
    def validate_output(self, result: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate output against all guardrails.
        
        Args:
            result: Processing result to validate
            
        Returns:
            Tuple of (is_valid, violations, sanitized_result)
        """
        violations = []
        sanitized_result = result.copy()
        
        # 1. Quality threshold check
        quality_score = result.get('quality_score', 0)
        if quality_score < self.min_quality_threshold:
            violations.append(
                f"Quality score {quality_score:.2f} below threshold {self.min_quality_threshold}"
            )
            logger.warning("Quality threshold violation",
                          quality_score=quality_score,
                          threshold=self.min_quality_threshold)
        
        # 2. Category restrictions
        if self.enable_category_restrictions:
            category = result.get('category', '')
            if self.blocked_categories and category in self.blocked_categories:
                violations.append(f"Category '{category}' is blocked")
                logger.warning("Blocked category detected", category=category)
            if self.allowed_categories and category not in self.allowed_categories:
                violations.append(f"Category '{category}' not in allowed list")
                logger.warning("Category not in allowed list", category=category)
        
        # 3. Content safety check
        if self.enable_content_filter:
            content_violations = self._check_content_safety(result)
            violations.extend(content_violations)
            if content_violations:
                logger.warning("Content safety violations detected", violations=content_violations)
        
        # 4. PII detection
        if self.enable_pii_detection:
            pii_found = self._detect_pii(result)
            if pii_found:
                violations.append(f"PII detected: {', '.join(pii_found)}")
                logger.warning("PII detected in output", pii_types=pii_found)
                # Sanitize PII
                sanitized_result = self._sanitize_pii(sanitized_result, pii_found)
        
        # 5. Output sanitization
        sanitized_result = self._sanitize_output(sanitized_result)
        
        # Add guardrail metadata
        sanitized_result['guardrails'] = {
            'passed': len(violations) == 0,
            'violations': violations,
            'violation_count': len(violations),
            'quality_threshold': self.min_quality_threshold,
            'pii_detected': bool(pii_found) if self.enable_pii_detection else False
        }
        
        is_valid = len(violations) == 0
        return is_valid, violations, sanitized_result
    
    def _check_content_safety(self, result: Dict[str, Any]) -> List[str]:
        """Check for harmful or inappropriate content."""
        violations = []
        text_content = ""
        
        # Collect all text content
        if result.get('raw_text'):
            text_content += result['raw_text'] + " "
        if result.get('visual_features'):
            text_content += result['visual_features'] + " "
        if result.get('labels'):
            text_content += json.dumps(result['labels']) + " "
        if result.get('category_reasoning'):
            text_content += result['category_reasoning'] + " "
        
        # Check against harmful patterns
        for pattern in self.harmful_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                violations.append(f"Harmful content pattern detected: {pattern}")
        
        return violations
    
    def _detect_pii(self, result: Dict[str, Any]) -> List[str]:
        """Detect personally identifiable information."""
        pii_found = []
        text_content = ""
        
        # Collect all text content
        if result.get('raw_text'):
            text_content += result['raw_text'] + " "
        if result.get('visual_features'):
            text_content += result['visual_features'] + " "
        if result.get('labels'):
            text_content += json.dumps(result['labels']) + " "
        
        # Check for PII patterns
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, text_content):
                pii_found.append(pii_type)
        
        return pii_found
    
    def _sanitize_pii(self, result: Dict[str, Any], pii_types: List[str]) -> Dict[str, Any]:
        """Sanitize PII from result."""
        sanitized = result.copy()
        
        # Redact PII from text fields
        for field in ['raw_text', 'visual_features']:
            if field in sanitized and sanitized[field]:
                text = sanitized[field]
                for pii_type in pii_types:
                    pattern = self.pii_patterns.get(pii_type, '')
                    if pattern:
                        text = re.sub(pattern, f'[REDACTED_{pii_type.upper()}]', text)
                sanitized[field] = text
        
        # Sanitize labels JSON
        if 'labels' in sanitized and sanitized['labels']:
            labels_str = json.dumps(sanitized['labels'])
            for pii_type in pii_types:
                pattern = self.pii_patterns.get(pii_type, '')
                if pattern:
                    labels_str = re.sub(pattern, f'[REDACTED_{pii_type.upper()}]', labels_str)
            try:
                sanitized['labels'] = json.loads(labels_str)
            except:
                pass  # Keep original if parsing fails
        
        logger.info("PII sanitized", pii_types=pii_types)
        return sanitized
    
    def _sanitize_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """General output sanitization."""
        sanitized = result.copy()
        
        # Remove or sanitize sensitive fields
        # Ensure no None values in critical fields
        if 'file_path' in sanitized:
            # Don't expose full file paths in output
            if sanitized['file_path']:
                sanitized['file_path'] = sanitized.get('file_name', 'file')
        
        # Ensure string fields are not too long
        max_text_length = 50000  # 50KB limit
        for field in ['raw_text', 'visual_features']:
            if field in sanitized and sanitized[field]:
                if len(sanitized[field]) > max_text_length:
                    sanitized[field] = sanitized[field][:max_text_length] + "... [TRUNCATED]"
                    logger.warning("Field truncated", field=field, length=len(sanitized[field]))
        
        return sanitized
    
    def filter_categories(self, category: str) -> bool:
        """
        Check if category is allowed.
        
        Args:
            category: Category to check
            
        Returns:
            True if allowed, False if blocked
        """
        if not self.enable_category_restrictions:
            return True
        
        if self.blocked_categories and category in self.blocked_categories:
            return False
        
        if self.allowed_categories and category not in self.allowed_categories:
            return False
        
        return True
    
    def validate_before_processing(self, file_path: str, file_name: str) -> Tuple[bool, List[str]]:
        """
        Validate file before processing.
        
        Args:
            file_path: Path to file
            file_name: Name of file
            
        Returns:
            Tuple of (is_allowed, violations)
        """
        violations = []
        
        # Check file name for suspicious patterns
        suspicious_patterns = [
            r'\.(exe|bat|cmd|scr|vbs|js)$',  # Executable files
            r'\.(zip|rar|7z|tar|gz)$',  # Archive files (could contain malware)
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, file_name, re.IGNORECASE):
                violations.append(f"File type not allowed: {file_name}")
        
        # Check file size (if needed)
        try:
            import os
            file_size = os.path.getsize(file_path)
            max_size = 100 * 1024 * 1024  # 100MB
            if file_size > max_size:
                violations.append(f"File size {file_size} exceeds maximum {max_size}")
        except:
            pass
        
        return len(violations) == 0, violations

