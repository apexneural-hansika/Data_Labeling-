# Quality Score Fix

## Issue
Quality scores were not being assigned to processing results.

## Root Cause
The supervisor agent's dynamic plan creation might skip the quality check step, or the quality score wasn't being properly merged into the final result structure.

## Solution

### 1. Supervisor Agent (`agentic_agents/supervisor.py`)
- Added automatic quality check at the end of plan execution if not already performed
- Ensures `quality_score` is always present in the state
- Creates default `quality_check` structure if missing
- Ensures `quality_score` is at the top level of the result

### 2. Orchestrator (`orchestrator_agentic.py`)
- Added fallback quality check if quality score is missing or zero
- Ensures `quality_check` structure is always present
- Ensures `quality_score` is at the top level for easy access
- Stores API keys for quality check agent initialization

### 3. Frontend (`static/script.js`)
- Already handles quality score display correctly
- Checks both `result.quality_check.quality_score` and `result.quality_score`

## Changes Made

### Supervisor Agent
```python
# After plan execution, ensure quality check is performed
if 'quality_score' not in state or state.get('quality_score', 0) == 0:
    # Perform quality check
    # Ensure quality_check structure exists
    # Ensure quality_score is at top level
```

### Orchestrator
```python
# Ensure quality_score is present in result
if 'quality_score' not in result or result.get('quality_score', 0) == 0:
    # Perform quality check
    # Create quality_check structure
    # Ensure quality_score is at top level
```

## Result Structure

Now all results will have:
```json
{
  "quality_score": 0.85,
  "quality_status": "high",
  "quality_check": {
    "quality_score": 0.85,
    "quality_status": "high",
    "issues": [],
    "passed": true,
    "recommendations": []
  }
}
```

## Testing

1. Upload a file through the frontend
2. Check the result JSON - should have `quality_score` and `quality_check`
3. Verify the quality score is displayed in the UI
4. Check server logs for quality check execution

## Notes

- Quality check is now guaranteed to run even if the supervisor's plan doesn't include it
- Quality score defaults to 0.0 if quality check fails
- Quality check uses the same QualityCheckAgent that validates:
  - Required fields presence
  - Content quality (text length, visual features)
  - Category assignment
  - Label completeness
  - Confidence scores



