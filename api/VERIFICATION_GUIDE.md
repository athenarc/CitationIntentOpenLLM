# Verifying Prompting Methods

This guide explains how to verify that your prompting method configuration (zero-shot, one-shot, few-shot, many-shot) is working correctly.

## Quick Verification

### Method 1: Using the verification script

```bash
# Start the API
python main.py

# In another terminal, run the verification script
python verify_prompting.py
```

The script will:
1. Fetch your current configuration
2. Inspect the actual system prompt being used
3. Verify the number of examples matches your settings
4. Show you a preview of the prompt structure

### Method 2: Using the /inspect-prompt endpoint

```bash
# Get detailed prompt information
curl http://localhost:8000/inspect-prompt | jq
```

This returns:
- Full system prompt messages array
- Number of messages
- Expected vs actual example counts
- Explanation of how examples are structured

### Method 3: Check each classification response

When you make a classification request, the response includes `prompt_info`:

```bash
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d @example_input.json | jq .prompt_info
```

Response includes:
```json
{
  "prompt_info": {
    "prompting_method": "few-shot",
    "examples_method": "1-inline",
    "num_messages_in_prompt": 1,
    "examples_per_class": 5,
    "total_expected_examples": 15
  }
}
```

## Understanding the Results

### Zero-shot
- **Expected messages**: 1 (just the system prompt)
- **No examples** in the prompt

### One-shot with inline (1-inline)
- **Expected messages**: 1
- System message contains `# EXAMPLES #` header
- 1 example per class (e.g., 3 for SciCite, 6 for ACL-ARC)

### Few-shot with inline (1-inline)
- **Expected messages**: 1
- System message contains `# EXAMPLES #` header
- 5 examples per class (e.g., 15 for SciCite, 30 for ACL-ARC)

### Few-shot with roles (2-roles)
- **Expected messages**: 1 + (5 examples × classes × 2)
  - SciCite: 1 + (5 × 3 × 2) = 31 messages
  - ACL-ARC: 1 + (5 × 6 × 2) = 61 messages
- System message followed by user/assistant pairs

### Many-shot with roles (2-roles)
- **Expected messages**: 1 + (10 examples × classes × 2)
  - SciCite: 1 + (10 × 3 × 2) = 61 messages
  - ACL-ARC: 1 + (10 × 6 × 2) = 121 messages

## Common Issues

### Issue: Wrong number of messages

**Problem**: `num_messages` doesn't match expected count

**Solution**: 
1. Check `config.json` for correct `prompting_method` and `examples_method`
2. Restart the API to reload configuration
3. Verify training data exists at `datasets/formatted/{dataset}/train.csv`

### Issue: No examples header in inline mode

**Problem**: Using `1-inline` but no `# EXAMPLES #` in system message

**Solution**: 
1. Verify `prompting_method` is not "zero-shot"
2. Check that training data is accessible
3. Look for errors in API logs

### Issue: Examples are identical

**Problem**: Same examples appear in different runs

**Solution**: This is expected! The `examples_seed` parameter (default: 42) ensures reproducible example selection. Change it in `config.json` for different examples.

## Configuration Examples

### Test different prompting methods

```bash
# Zero-shot (baseline)
sed -i '' 's/"prompting_method": ".*"/"prompting_method": "zero-shot"/' config.json
python verify_prompting.py

# One-shot
sed -i '' 's/"prompting_method": ".*"/"prompting_method": "one-shot"/' config.json
python verify_prompting.py

# Few-shot inline
sed -i '' 's/"prompting_method": ".*"/"prompting_method": "few-shot"/' config.json
sed -i '' 's/"examples_method": ".*"/"examples_method": "1-inline"/' config.json
python verify_prompting.py

# Few-shot roles
sed -i '' 's/"examples_method": ".*"/"examples_method": "2-roles"/' config.json
python verify_prompting.py
```

## Debugging Tips

1. **Check API startup logs**: Look for "Initialized classifier" messages
2. **Verify training data**: `ls -lh datasets/formatted/scicite/train.csv`
3. **Test with /inspect-prompt**: Returns full prompt structure
4. **Compare with experiments**: The logic matches `citation_intent_classification_experiments.py`

## Advanced: Inspecting Prompt Content

To see the full prompt (including all examples):

```python
import requests

response = requests.get("http://localhost:8000/inspect-prompt")
prompt = response.json()

# Print full system message (for inline method)
if prompt['examples_method'] == '1-inline':
    print(prompt['system_prompt'][0]['content'])

# Print all messages (for roles method)
else:
    for i, msg in enumerate(prompt['system_prompt']):
        print(f"\n--- Message {i+1} [{msg['role']}] ---")
        print(msg['content'])
```
