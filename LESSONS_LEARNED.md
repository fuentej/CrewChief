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

### 6. Keys with Missing Values
**Issue:** Truncation could leave keys without values (e.g., `"recommended_items":` with nothing after the colon).
**Root Cause:** Truncation happened mid-field, leaving the key but removing the entire value.
**Learning:** Need to detect not just unterminated strings but also incomplete key-value pairs where the key exists but value doesn't.

### 7. Entire Missing Fields
**Issue:** Some truncations removed entire fields from the JSON (e.g., no `"recommended_items"` key at all).
**Root Cause:** Truncation happened at a boundary where a field simply wasn't included in the partial response.
**Learning:** When Pydantic validation reports missing fields, they can often be filled with sensible defaults (empty arrays for list fields).

### 8. Fallback Request Formatting
**Issue:** Fallback requests to fill missing fields were returning markdown-wrapped JSON that regex couldn't parse.
**Root Cause:** The LLM consistently wraps responses in ` ```json ... ``` ` even when asked for raw JSON.
**Learning:** Always handle markdown wrapping in both primary and fallback requests. Can't assume "raw" requests will truly be raw.

## Solutions Implemented

### 1. Robust JSON Boundary Detection
- Track nesting depth while respecting string boundaries
- Count braces/brackets only when not inside a string
- Handle escape sequences properly

### 2. Two-Stage Markdown Removal
- Remove markdown in initial extraction (happy path)
- **Also** remove markdown in error handling (when initial parsing fails)
- This ensures both paths work with clean JSON
- Handle markdown in both direct JSON responses and fallback requests

### 3. Intelligent Truncation Recovery
- Detect unterminated strings (odd quote count)
- Detect keys with missing values (e.g., `"key":` with no value)
- Backtrack to the last complete value in nested structures
- Remove trailing commas that would make arrays/objects invalid
- Preserve structure integrity

### 4. Multiple Repair Strategies
- Try different closure orders (brackets-first vs braces-first)
- Detect and fill missing required fields with empty array defaults
- Add missing fields when Pydantic validation reports them as missing
- Validate each repair attempt with the actual schema

### 5. Fallback Field Requests
- When critical fields are empty after repair, make separate targeted requests
- Request only the missing field (e.g., "Generate only a JSON array of...")
- This ensures complete responses even if initial request truncates
- Gracefully handle markdown-wrapped responses in fallback requests

### 6. Graceful Degradation
- Maintain detailed error messages with both the original and fixed JSON
- Show character counts and sample content for debugging
- Allow the app to continue even with incomplete responses
- Use empty arrays/objects as defaults when repair fails

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

## Lessons for Multi-Step LLM Integration

### When to Use Multiple Requests Instead of Repair
While JSON repair is powerful, sometimes it's better to request data in smaller pieces:

1. **For complex structured responses:** Request each major field separately rather than everything at once
2. **For content that's inherently variable:** LLM responses vary in length; asking for fixed-size pieces is more predictable
3. **For local/fast LLMs:** Since there's no network latency, multiple requests are cheap - worth it for reliability
4. **When repair becomes complex:** If repair logic is getting convoluted, split into simpler focused requests

### Trade-offs
- **Pros:** Simpler repair logic, better chance of complete data, easier to validate each piece
- **Cons:** Multiple round-trips (minor cost for local LLMs), need to orchestrate fallback requests carefully

For CrewChief's `track-prep`, we use both approaches:
1. **Primary request:** Ask for complete `TrackPrepChecklist` with all fields (fast path)
2. **Fallback requests:** If fields are empty/missing, make targeted requests for just those fields (robustness)

This hybrid approach gives us both speed and reliability.

## Conclusion
Integrating with external LLM services requires defensive programming. Responses may be incomplete, malformed, or wrapped in unexpected formatting. A robust solution layers multiple recovery strategies:
1. Try to parse responses as-is
2. Repair truncated/malformed JSON
3. Fill missing fields with defaults
4. Make targeted fallback requests for missing data

The key lessons:
- **Never trust external data** to be in the exact format you expect
- **Build in recovery mechanisms** at multiple levels
- **Validate at each step** - don't assume a fix will work
- **For local services, don't optimize for latency** - multiple requests can improve reliability significantly
- **Always handle markdown** - even when you ask for raw JSON, you'll get markdown wrapped responses
