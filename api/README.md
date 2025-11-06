# Citation Intent Classification API

A production-ready REST API for classifying citation intents in scientific papers using open-source LLMs.

## Quick Start

### 1. Install Dependencies

```
cd api
pip install -r requirements.txt

```

### 2. Start vLLM Server

```
pip install vllm
vllm serve Qwen/Qwen2.5-14B-Instruct --port 8080

```

> Other OpenAI-compatible servers (TGI, LM Studio, OpenAI) are also supported.
> 

### 3. Configure

Edit `config/config.json` with your server URL and model name.

```
{
    "inference_api": {
        "base_url": "http://localhost:8080/v1",
        "api_key": "",
        "model_name": "Qwen/Qwen2.5-14B-Instruct"
    },
    "dataset": "scicite",
    "system_prompt_id": 3,
    "prompting_method": "zero-shot",
    "examples_method": "1-inline",
    "examples_seed": 42,
    "query_template": "1-simple",
    "temperature": 0.0,
    "max_tokens": 15
}

```

### 4. Start the API

```
# Development
python src/main.py

# Production
bash scripts/gunicorn.sh

```

API at: http://localhost:8000

Docs at: http://localhost:8000/docs

### 5. Test

Visit `http://localhost:8000/docs` or:

```
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Recent work has shown that neural networks can learn (Smith et al., 2020).",
    "cite_start": 52,
    "cite_end": 72
  }'

```

## Configuration

### Datasets

**SciCite (3 classes):**

- `background information` - Background context
- `method` - Using a method/tool/dataset
- `results comparison` - Comparing results

**ACL-ARC (6 classes):**

- `BACKGROUND`, `MOTIVATION`, `USES`, `EXTENDS`, `COMPARES_CONTRASTS`, `FUTURE`

### Prompting Methods

- `zero-shot`: No examples (fastest)
- `one-shot`: 1 example per class
- `few-shot`: 5 examples per class (recommended)
- `many-shot`: 10 examples per class (best accuracy)

**Example injection:**

- `1-inline`: Appends to system prompt
- `2-roles`: User/assistant conversation pairs

### System Prompts

- **SP1**: Minimal
- **SP2**: Structured
- **SP3**: Explicit (recommended)

## API Endpoints

### POST /classify

Classify a citation's intent.

```
{
  "text": "Full text containing citation",
  "cite_start": 100,
  "cite_end": 120
}

```

### GET /config

View current configuration.

### GET /inspect-prompt

Inspect system prompt with examples.

### GET /health

Health check.

### GET /docs

Interactive Swagger UI documentation.

## Usage Examples

### Python

```
import requests

response = requests.post(
    "http://localhost:8000/classify",
    json={
        "text": "... (Smith et al., 2020).",
        "cite_start": 52,
        "cite_end": 72
    }
)
print(response.json()["predicted_class"])

```

### cURL

```
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d @tests/example_input.json

```

## Production Deployment

```
# Start
bash scripts/gunicorn.sh

# Stop
bash scripts/stop.sh

```

**Environment variables** (`.env`):

```
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=info
WORKERS=4

```

**Logs:**

- Access: `logs/access.log`
- Error: `logs/error.log`
- PID: `logs/gunicorn.pid`

## Verification

```
# Verify prompting setup
python scripts/verify_prompting.py

# Verify directory structure
python scripts/verify_structure.py

# Run tests
python tests/test_api.py

```

## Troubleshooting

### Startup Failures

The `gunicorn.sh` script includes automatic diagnostics:

**Port already in use:**
```bash
# Script will show which process is using the port
# Kill it with:
kill $(lsof -t -i:8000)
```

**Import errors:**
```bash
# Check logs/import_error.log for details
cat logs/import_error.log

# Test imports manually:
python -c "from src.main import app"
```

**Process dies immediately:**
```bash
# Check error logs:
tail -20 logs/error.log

# Run in foreground for debugging:
gunicorn src.main:app --bind 0.0.0.0:8000 --log-level debug
```

### Runtime Issues

**Port conflicts:**
```bash
uvicorn src.main:app --port 8001
```

**Connection issues:**
- Check server: `curl http://localhost:8080/v1/models`
- Verify `base_url` ends with `/v1`

**Invalid predictions:**
- Use `temperature: 0.0`
- Try `system_prompt_id: 3`
- Use `query_template: "2-qa-multiple-choice"`

## Citation Format

Citations are preprocessed with `@@CITATION@@` tag:

```
Input:  "... can learn (Smith et al., 2020)."
Output: "... can learn @@CITATION@@."

```

## Architecture

```
api/
├── config/           # Configuration files
├── data/             # Training data for few-shot
├── src/              # Source code
├── scripts/          # Deployment scripts
├── tests/            # Test suite
└── README.md

```

## Development

```
# Auto-reload
uvicorn src.main:app --reload

# Debug logging
LOG_LEVEL=debug python src.main.py

```

## License

Same as main CitationIntentOpenLLM project.
