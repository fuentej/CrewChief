# Lessons Learned: LLM JSON Response Handling

## Overview
This document captures lessons learned while debugging and fixing JSON parsing issues with LLM responses from Foundry Local in the CrewChief project.

## The Problem
The `track-prep` command was failing with JSON validation errors when parsing LLM responses. After extensive investigation, we discovered the root cause was **Foundry Local truncating responses at exactly 621 characters**, producing incomplete JSON with:
- Unterminated strings (odd number of quotes)
- Unclosed arrays and objects
- Markdown code block wrapping (```json ... ```)

## Key Issues Encountered

### 1. Response Truncation at Fixed Limit
**Issue:** Foundry Local was cutting off responses mid-word, always at 621 characters.
**Root Cause:** Likely a configuration limit in Foundry Local (max_tokens or response_length).
**Learning:** External service limits can silently break your application. Always validate external API responses gracefully.

### 2. Markdown Code Block Handling
**Issue:** LLM responses were wrapped in triple backticks (```json ... ```), but our JSON extraction logic wasn't accounting for this in the error path.
**Root Cause:** The markdown removal was only in the happy path; when initial parsing failed, we tried to fix truncated JSON without first removing the backticks.
**Learning:** Error handling paths need the same cleanup and normalization as the happy path. Don't assume the data is in the same state.

### 3. Brace/Bracket Counting vs. Proper Nesting Depth
**Issue:** Initial attempts to find JSON boundaries by counting braces globally didn't account for nested structures.
Example: Finding the first `]` that closes an array instead of the final `}` that closes the root object.
**Root Cause:** Simple counting doesn't respect structure boundaries.
**Learning:** When parsing structured data, track depth/nesting state properly. String boundaries matter - don't count quotes inside strings.

### 4. Incomplete String Truncation
**Issue:** When JSON was cut off mid-string, we needed to remove the incomplete value and any trailing commas.
**Root Cause:** Removing the unterminated string but keeping the comma left invalid JSON like `[value1, value2,]`.
**Learning:** When truncating incomplete values, also remove associated punctuation (commas, colons) to maintain valid structure.

### 5. Multiple Closure Strategies
**Issue:** Closing arrays and objects in the wrong order could still produce invalid JSON.
Example: `]}` vs `}]` depending on nesting order.
**Root Cause:** Different JSON structures require different closure patterns.
**Learning:** When fixing incomplete data, try multiple repair strategies and validate each attempt rather than assuming one approach will work.

## Solutions Implemented

### 1. Robust JSON Boundary Detection
- Track nesting depth while respecting string boundaries
- Count braces/brackets only when not inside a string
- Handle escape sequences properly

### 2. Two-Stage Markdown Removal
- Remove markdown in initial extraction (happy path)
- **Also** remove markdown in error handling (when initial parsing fails)
- This ensures both paths work with clean JSON

### 3. Intelligent Truncation
- Detect unterminated strings (odd quote count)
- Backtrack to the last complete value
- Remove trailing commas that would make arrays/objects invalid
- Preserve structure integrity

### 4. Closure Validation
- Try multiple closure orders (brackets-first vs braces-first)
- Validate each attempt with the actual Pydantic schema
- Only accept closures that pass validation

### 5. Graceful Degradation
- Maintain detailed error messages with both the original and fixed JSON
- Show character counts and sample content for debugging
- Allow the app to continue even with incomplete responses

## Code Architecture Improvements

### Error Handling Pattern
```python
try:
    # Try to parse JSON as-is
    return parse_json(json_str)
except JSONDecodeError:
    # Multi-step recovery:
    # 1. Remove markdown markers
    # 2. Detect and fix incomplete strings
    # 3. Close open structures
    # 4. Try validation with multiple closure strategies
    fixed_json = repair_json(json_str)
    return parse_json(fixed_json)
```

### Key Functions Created
1. **Markdown removal with JSON boundary detection**
   - Finds actual JSON start `{` or `[` within markdown
   - Tracks nesting depth to find matching close
   - Handles string boundaries correctly

2. **Incomplete string detection and removal**
   - Counts quotes to detect unterminated strings
   - Backtracks to last complete value
   - Removes trailing commas

3. **Multiple closure strategy validator**
   - Tries different bracket/brace closure orders
   - Validates each attempt immediately
   - Returns first successful parse

## Prevention Strategies

### For This Project
1. **Configuration tuning:** Check Foundry Local's max token/response length settings and increase if needed
2. **Response size limits:** Add explicit checks before parsing to warn on truncated responses
3. **Timeout handling:** Monitor response times to detect truncation issues earlier
4. **Validation layer:** Implement comprehensive JSON schema validation with helpful error messages

### For Future LLM Integration Projects
1. **Assume network services can fail in weird ways**
   - Responses can be incomplete
   - Responses can be malformed
   - Services can have undocumented limits

2. **Implement defense-in-depth**
   - Validate data at multiple stages
   - Have fallback repair strategies
   - Log everything for debugging

3. **Test edge cases**
   - Test truncated JSON
   - Test malformed markdown
   - Test deeply nested structures
   - Test various character encodings

4. **Make errors actionable**
   - Include raw response samples in error messages
   - Show what was fixed and how
   - Provide debugging hints for common issues

## Files Modified
- `crewchief/llm.py` - Core JSON parsing and error recovery logic
- `crewchief/cli.py` - Enhanced error output with full tracebacks
- `crewchief/prompts/track_prep.txt` - Fixed escaped braces for Python format()

## Testing Recommendations
1. Unit tests for JSON repair functions with various truncation scenarios
2. Integration tests with actual Foundry Local to verify edge cases
3. Fuzzing tests with randomly truncated JSON
4. Performance tests to ensure repair logic doesn't add significant overhead

## Conclusion
Integrating with external LLM services requires defensive programming. Responses may be incomplete, malformed, or wrapped in unexpected formatting. A robust solution layers multiple recovery strategies and validates at each step, allowing graceful degradation when ideal conditions aren't met.

The key lesson: **never trust external data to be in the exact format you expect**. Build in recovery mechanisms and detailed logging to help diagnose issues when they occur.
