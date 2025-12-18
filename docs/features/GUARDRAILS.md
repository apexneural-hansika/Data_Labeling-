# Guardrails System Documentation

## Overview

The guardrails system provides content safety, validation, and output filtering to ensure secure and compliant operation of the data labeling system.

## Features

### 1. Quality Threshold Guardrail ✅
- Enforces minimum quality score for outputs
- Rejects results below threshold
- Configurable threshold (default: 0.6)

### 2. PII Detection & Sanitization ✅
- Detects personally identifiable information:
  - Email addresses
  - Phone numbers
  - Social Security Numbers (SSN)
  - Credit card numbers
  - IP addresses
  - Passport numbers
- Automatically redacts PII from outputs
- Logs PII detection for audit

### 3. Content Safety Filter ✅
- Detects harmful or inappropriate content patterns
- Blocks content containing:
  - Violence-related terms
  - Hate speech indicators
  - Illegal activity references
  - Self-harm references
- Customizable pattern matching

### 4. Category Restrictions ✅
- Block specific categories
- Allow only specific categories
- Category validation before processing

### 5. Output Sanitization ✅
- Removes sensitive file paths
- Truncates overly long text fields
- Ensures safe output format

### 6. Pre-Processing Validation ✅
- Validates files before processing
- Blocks suspicious file types
- Enforces file size limits

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# Enable/Disable Guardrails
ENABLE_GUARDRAILS=true
ENABLE_CONTENT_FILTER=true
ENABLE_PII_DETECTION=true
ENABLE_CATEGORY_RESTRICTIONS=false

# Quality Threshold
MIN_QUALITY_THRESHOLD=0.6

# Category Restrictions (comma-separated)
BLOCKED_CATEGORIES=inappropriate,harmful,illegal
ALLOWED_CATEGORIES=document_processing,image_analysis,audio_transcription
```

### In Code

```python
from utils.guardrails import Guardrails

guardrails = Guardrails(
    enable_content_filter=True,
    enable_pii_detection=True,
    enable_category_restrictions=True,
    blocked_categories=['inappropriate', 'harmful'],
    allowed_categories=['document_processing', 'image_analysis'],
    min_quality_threshold=0.7
)
```

## How It Works

### During Processing

1. **Pre-Processing Check**:
   - File type validation
   - File size check
   - Suspicious pattern detection

2. **Post-Processing Validation**:
   - Quality threshold check
   - Category validation
   - Content safety check
   - PII detection and sanitization
   - Output sanitization

3. **Result Enhancement**:
   - Adds `guardrails` metadata to result
   - Includes violation list if any
   - Provides sanitized output

### Output Structure

Results include guardrail metadata:

```json
{
  "file_name": "test.pdf",
  "modality": "text_document",
  "category": "document_processing",
  "quality_score": 0.85,
  "guardrails": {
    "passed": true,
    "violations": [],
    "violation_count": 0,
    "quality_threshold": 0.6,
    "pii_detected": false
  }
}
```

If violations are detected:

```json
{
  "guardrails": {
    "passed": false,
    "violations": [
      "PII detected: email, phone",
      "Quality score 0.55 below threshold 0.6"
    ],
    "violation_count": 2,
    "quality_threshold": 0.6,
    "pii_detected": true
  },
  "raw_text": "Contact [REDACTED_EMAIL] or [REDACTED_PHONE]"
}
```

## Usage Examples

### Basic Usage

Guardrails are automatically applied when processing files:

```python
from orchestrator_agentic import AgenticOrchestrator

orchestrator = AgenticOrchestrator(...)
result = orchestrator.process_file('file.pdf')

# Check guardrail status
if result.get('guardrail_passed'):
    print("Output passed guardrails")
else:
    print(f"Violations: {result.get('guardrails', {}).get('violations', [])}")
```

### Custom Guardrails

```python
from utils.guardrails import Guardrails

# Create custom guardrails
guardrails = Guardrails(
    min_quality_threshold=0.8,
    blocked_categories=['inappropriate'],
    enable_pii_detection=True
)

# Validate result
is_valid, violations, sanitized = guardrails.validate_output(result)
```

### Pre-Processing Check

```python
# Check file before processing
is_allowed, violations = guardrails.validate_before_processing(
    file_path='uploads/file.pdf',
    file_name='file.pdf'
)

if not is_allowed:
    print(f"File rejected: {violations}")
```

## Testing

Run the guardrails test suite:

```bash
python test_scripts/test_guardrails.py
```

## Customization

### Adding Custom Patterns

Edit `utils/guardrails.py`:

```python
# Add to harmful_patterns
self.harmful_patterns = [
    r'\b(your_pattern_here)\b',
    # ... existing patterns
]

# Add to pii_patterns
self.pii_patterns = {
    'custom_pii': r'your_regex_pattern',
    # ... existing patterns
}
```

### Custom Validation Rules

Extend the `Guardrails` class:

```python
class CustomGuardrails(Guardrails):
    def validate_output(self, result):
        # Call parent validation
        is_valid, violations, sanitized = super().validate_output(result)
        
        # Add custom checks
        if self._custom_check(result):
            violations.append("Custom violation")
            is_valid = False
        
        return is_valid, violations, sanitized
```

## Best Practices

1. **Enable PII Detection** in production
2. **Set Quality Threshold** based on your requirements
3. **Configure Category Restrictions** for domain-specific needs
4. **Monitor Violations** via logs
5. **Review Sanitized Outputs** to ensure proper redaction

## Security Considerations

- **PII Redaction**: PII is redacted but original is logged (for audit)
- **Content Filtering**: Pattern-based, may need tuning for your use case
- **Category Restrictions**: Enforced at validation time
- **Quality Threshold**: Prevents low-quality outputs from being stored

## Troubleshooting

### Guardrails Not Working
- Check `ENABLE_GUARDRAILS=true` in config
- Verify guardrails are initialized in orchestrator
- Check logs for initialization errors

### False Positives
- Adjust pattern matching in `harmful_patterns`
- Tune quality threshold
- Review category restrictions

### PII Not Detected
- Verify `ENABLE_PII_DETECTION=true`
- Check PII patterns match your data format
- Review sanitized output

## API Integration

Guardrails are automatically applied to all processed files. Check the result:

```bash
curl -X POST http://localhost:5000/api/upload -F "file=@test.pdf"
```

Response includes guardrail status:

```json
{
  "success": true,
  "guardrail_passed": true,
  "guardrails": {
    "passed": true,
    "violations": []
  }
}
```

## Summary

The guardrails system provides:
- ✅ Content safety filtering
- ✅ PII detection and sanitization
- ✅ Quality threshold enforcement
- ✅ Category restrictions
- ✅ Output sanitization
- ✅ Pre-processing validation

All guardrails are configurable and can be enabled/disabled as needed!

