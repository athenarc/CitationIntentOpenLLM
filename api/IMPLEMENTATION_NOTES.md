# Few-Shot Prompting Support - Implementation Summary

## Overview

Added support for zero-shot, one-shot, few-shot, and many-shot prompting methods to the Citation Intent Classification API, matching the experimental pipeline configuration.

## Changes Made

### 1. Configuration (`config.json`)

Added three new parameters:

```json
{
    "prompting_method": "zero-shot",     // "zero-shot" | "one-shot" | "few-shot" | "many-shot"
    "examples_method": "1-inline",       // "1-inline" | "2-roles"
    "examples_seed": 42                  // Random seed for example selection
}
```

**Prompting methods:**
- `zero-shot`: 0 examples (default)
- `one-shot`: 1 example per class
- `few-shot`: 5 examples per class
- `many-shot`: 10 examples per class

**Examples injection methods:**
- `1-inline`: Appends examples to system prompt with `# EXAMPLES #` header
- `2-roles`: Injects as alternating user/assistant message pairs in conversation history

### 2. Classifier (`classifier.py`)

Added four new helper functions:

- `get_num_examples(prompting_method)`: Maps prompting method to number of examples
- `load_training_data(dataset)`: Loads training CSV for example selection
- `add_examples(...)`: Core function that injects examples into system prompt (matches experimental code)

Updated `CitationIntentClassifier.__init__()`:
- Checks `prompting_method` configuration
- If not zero-shot, loads training data and adds examples to system prompt
- Supports both inline and roles-based example injection

### 3. API Endpoints (`main.py`)

Updated `ConfigResponse` model to include:
- `prompting_method`: Current prompting strategy
- `examples_method`: How examples are injected

Updated `/config` endpoint to return these new fields.

Added logging configuration that reads from `LOG_LEVEL` environment variable.

### 4. Dependencies (`requirements.txt`)

Added:
- `pandas>=1.5.0` (required for loading training data)
- `gunicorn>=21.0.0` (for production deployment)

### 5. Production Deployment

Created two new scripts:

**`gunicorn.sh`**: Production startup script
- Runs with Gunicorn + UvicornWorker
- Configurable workers, timeouts, logging
- Daemon mode with PID tracking
- Creates `logs/` directory with access/error logs

**`stop.sh`**: Graceful shutdown script
- Reads PID from logs/gunicorn.pid
- Attempts graceful shutdown (SIGTERM)
- Falls back to force kill if needed

Updated `main.py`:
- Added proper logging configuration
- Reads `API_HOST`, `API_PORT`, `LOG_LEVEL` from environment
- Enhanced error handling on startup

### 6. Documentation

Updated `README.md`:
- Added prompting strategy section
- Documented all three new parameters with examples
- Organized config params into logical groups

Updated `QUICKSTART.md`:
- Added prompting method examples
- Reference to `config.examples.json`

Created `config.examples.json`:
- Shows 4 different configuration patterns
- Zero-shot simple, few-shot QA, few-shot roles, many-shot ACL-ARC

## Usage Examples

### Zero-shot (default)
```json
{
    "prompting_method": "zero-shot",
    "examples_method": "1-inline",
    "query_template": "1-simple"
}
```
System prompt contains only task description, no examples.

### Few-shot with inline examples
```json
{
    "prompting_method": "few-shot",
    "examples_method": "1-inline",
    "query_template": "1-simple"
}
```
System prompt includes 5 examples per class appended as text.

### Few-shot with role-based examples
```json
{
    "prompting_method": "few-shot",
    "examples_method": "2-roles",
    "query_template": "2-qa-multiple-choice"
}
```
Conversation history includes 5 user/assistant pairs per class before the actual query.

### Many-shot for ACL-ARC
```json
{
    "dataset": "acl-arc",
    "prompting_method": "many-shot",
    "examples_method": "2-roles"
}
```
Conversation includes 10 examples per class (60 total examples for ACL-ARC's 6 classes).

## Testing

The implementation:
1. Reuses exact logic from `citation_intent_classification_experiments.py`
2. Loads training data from `datasets/formatted/{dataset}/train.csv`
3. Uses same random seed for reproducible example selection
4. Supports both datasets (SciCite, ACL-ARC)
5. Works with both query templates (simple, multiple-choice)

## Production Deployment

Start with Gunicorn:
```bash
cd api
./gunicorn.sh
```

Stop server:
```bash
./stop.sh
```

Logs available in:
- `logs/access.log`
- `logs/error.log`
- `logs/gunicorn.pid`

## Backward Compatibility

All new parameters have defaults:
- `prompting_method`: defaults to `"zero-shot"`
- `examples_method`: defaults to `"1-inline"`
- `examples_seed`: defaults to `42`

Existing configs without these fields will work as zero-shot (original behavior).
